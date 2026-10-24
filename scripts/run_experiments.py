import argparse
import csv
import os
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

PROFILES = {
    "Perfil1_Leitura": "Perfil1Leitura",
    "Perfil2_Escrita": "Perfil2Escrita",
}

SCENARIOS = {
    "CenarioA_Leve": 30,
    "CenarioB_Moderado": 80,
    "CenarioC_Elevado": 150,
}

MONITORED_SERVICES = [
    "api-gateway",
    "customers-service",
    "vets-service",
    "visits-service",
    "discovery-server",
]


def sample_docker_cpu(output_csv: Path, warmup_seconds: int, stop_event: threading.Event, interval: float = 2.0):
    # Aguarda o aquecimento antes de iniciar a coleta de CPU e memoria dos containers
    start_time = time.time()
    while not stop_event.is_set():
        if time.time() - start_time >= warmup_seconds:
            break
        time.sleep(0.5)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "elapsed_s", "service", "cpu_percent", "mem_percent", "mem_usage"])

        while not stop_event.is_set():
            ts = datetime.now().isoformat(timespec="seconds")
            elapsed = round(time.time() - start_time, 1)
            try:
                cmd = [
                    "docker", "stats", "--no-stream",
                    "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}|{{.MemUsage}}"
                ] + MONITORED_SERVICES
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    for line in res.stdout.strip().splitlines():
                        parts = line.split("|")
                        if len(parts) == 4:
                            name = parts[0].strip()
                            cpu_str = parts[1].strip().replace("%", "").replace(",", ".")
                            mem_str = parts[2].strip().replace("%", "").replace(",", ".")
                            mem_usage = parts[3].strip()
                            try:
                                cpu_val = float(cpu_str)
                            except ValueError:
                                cpu_val = 0.0
                            try:
                                mem_val = float(mem_str)
                            except ValueError:
                                mem_val = 0.0
                            writer.writerow([ts, elapsed, name, cpu_val, mem_val, mem_usage])
                    f.flush()
            except Exception as exc:
                print(f"[WARN] Falha ao coletar docker stats: {exc}", flush=True)

            stop_event.wait(interval)


def run_single_execution(
    host: str,
    profile_key: str,
    locust_class: str,
    scenario_key: str,
    users: int,
    rep: int,
    duration_s: int,
    warmup_s: int,
    raw_dir: Path,
    spawn_rate: int = 10,
):
    # Executa uma repeticao no Locust e salva os CSVs de metricas e de CPU
    prefix = f"{profile_key}_{scenario_key}_rep{rep:02d}"
    stats_file = raw_dir / f"{prefix}_stats.csv"
    cpu_file = raw_dir / f"{prefix}_cpu.csv"
    done_file = raw_dir / f"{prefix}.done"

    if done_file.exists() and stats_file.exists() and cpu_file.exists():
        print(f"[SKIP] {prefix} ja concluido.", flush=True)
        return "skipped"

    for partial in raw_dir.glob(f"{prefix}*"):
        try:
            partial.unlink()
        except OSError:
            pass

    print(
        f"\n[INICIO {datetime.now().strftime('%H:%M:%S')}] {prefix} | "
        f"Classe={locust_class} | Usuarios={users} | Duracao={duration_s}s",
        flush=True,
    )

    stop_event = threading.Event()
    cpu_thread = threading.Thread(
        target=sample_docker_cpu,
        args=(cpu_file, warmup_s, stop_event, 2.0),
        daemon=True,
    )
    cpu_thread.start()

    env = os.environ.copy()
    env["LOCUST_WARMUP_SECONDS"] = str(warmup_s)

    csv_base = str(raw_dir / prefix)
    effective_spawn_rate = max(spawn_rate, min(users, 25))

    cmd = [
        sys.executable, "-m", "locust",
        "-f", "locustfile.py",
        locust_class,
        "--headless",
        "--host", host,
        "-u", str(users),
        "-r", str(effective_spawn_rate),
        "-t", f"{duration_s}s",
        "--csv", csv_base,
        "--csv-full-history",
        "--only-summary",
        "--exit-code-on-error", "0",
    ]

    try:
        result = subprocess.run(cmd, env=env)
        success = (result.returncode in (0, 1)) and stats_file.exists()
    finally:
        stop_event.set()
        cpu_thread.join(timeout=5)

    if success:
        done_file.write_text(datetime.now().isoformat(), encoding="utf-8")
        print(f"[CONCLUIDO {datetime.now().strftime('%H:%M:%S')}] {prefix} salvo.", flush=True)
        try:
            subprocess.run([sys.executable, "scripts/analyze_results.py"], check=False)
        except Exception as exc:
            print(f"[WARN] Erro ao atualizar graficos: {exc}", flush=True)
        return "completed"
    return "failed"


def main():
    parser = argparse.ArgumentParser(description="Executa os cenarios experimentais no Locust.")
    parser.add_argument("--host", default="http://localhost:8085", help="URL do API Gateway")
    parser.add_argument("--repetitions", type=int, default=10, help="Repeticoes por cenario")
    parser.add_argument("--duration", type=int, default=360, help="Duracao de cada execucao em segundos")
    parser.add_argument("--warmup", type=int, default=60, help="Tempo de aquecimento em segundos")
    parser.add_argument("--cooldown", type=int, default=5, help="Intervalo entre execucoes em segundos")
    parser.add_argument("--raw-dir", default="results/raw", help="Diretorio de saida dos CSVs brutos")
    parser.add_argument("--profiles", nargs="*", choices=list(PROFILES.keys()), default=list(PROFILES.keys()))
    parser.add_argument("--scenarios", nargs="*", choices=list(SCENARIOS.keys()), default=list(SCENARIOS.keys()))
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        urllib.request.urlopen(f"{args.host}/api/vet/vets", timeout=5).read()
    except Exception as exc:
        print(f"[ERRO] Sem acesso ao API Gateway em {args.host}: {exc}", flush=True)
        sys.exit(1)

    chk = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True)
    if chk.returncode != 0:
        print(f"[ERRO] Sem acesso ao Docker: {chk.stderr.strip()}", flush=True)
        sys.exit(1)

    total_runs = len(args.profiles) * len(args.scenarios) * args.repetitions
    current_run = 0

    print(f"Iniciando bateria de testes: {total_runs} execucoes.", flush=True)
    for rep in range(1, args.repetitions + 1):
        for profile_key in args.profiles:
            locust_class = PROFILES[profile_key]
            for scenario_key in args.scenarios:
                users = SCENARIOS[scenario_key]
                current_run += 1
                print(f"\nProgresso: [{current_run}/{total_runs}] (Rodada {rep}/{args.repetitions})", flush=True)
                status = run_single_execution(
                    host=args.host,
                    profile_key=profile_key,
                    locust_class=locust_class,
                    scenario_key=scenario_key,
                    users=users,
                    rep=rep,
                    duration_s=args.duration,
                    warmup_s=args.warmup,
                    raw_dir=raw_dir,
                )
                if status == "completed" and current_run < total_runs and args.cooldown > 0:
                    time.sleep(args.cooldown)

    print("\nExecucoes finalizadas.", flush=True)


if __name__ == "__main__":
    main()
