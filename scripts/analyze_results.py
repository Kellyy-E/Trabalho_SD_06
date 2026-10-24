import re
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["figure.dpi"] = 150
plt.rcParams["font.size"] = 10
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3

PROFILE_LABELS = {
    "Perfil1_Leitura": "Perfil 1 - Leitura",
    "Perfil2_Escrita": "Perfil 2 - Escrita",
}

SCENARIO_ORDER = ["CenarioA_Leve", "CenarioB_Moderado", "CenarioC_Elevado"]
SCENARIO_LABELS = {
    "CenarioA_Leve": "A - Leve (30 usu.)",
    "CenarioB_Moderado": "B - Moderado (80 usu.)",
    "CenarioC_Elevado": "C - Elevado (150 usu.)",
}
SCENARIO_USERS = {
    "CenarioA_Leve": 30,
    "CenarioB_Moderado": 80,
    "CenarioC_Elevado": 150,
}

FILE_PATTERN = re.compile(r"^(Perfil[12]_[A-Za-z]+)_(Cenario[ABC]_[A-Za-z]+)_rep(\d+)_stats\.csv$")


def load_raw_results(raw_dir: Path):
    # Carrega os CSVs brutos do Locust e de CPU de cada repeticao concluida
    overall_rows = []
    operation_rows = []
    cpu_rows = []

    has_done_markers = any(raw_dir.glob("*.done"))

    for stats_path in sorted(raw_dir.glob("*_stats.csv")):
        match = FILE_PATTERN.match(stats_path.name)
        if not match:
            continue

        profile_key, scenario_key, rep_str = match.groups()
        rep = int(rep_str)
        prefix = f"{profile_key}_{scenario_key}_rep{rep_str}"
        done_path = raw_dir / f"{prefix}.done"
        if has_done_markers and not done_path.exists():
            continue
        cpu_path = raw_dir / f"{prefix}_cpu.csv"

        df = pd.read_csv(stats_path)
        if df.empty:
            continue

        cpu_by_service = {}
        if cpu_path.exists():
            try:
                cpu_df = pd.read_csv(cpu_path)
                if not cpu_df.empty and "service" in cpu_df.columns:
                    grouped_cpu = cpu_df.groupby("service")["cpu_percent"].mean().to_dict()
                    cpu_by_service = grouped_cpu
                    for svc, cpu_val in grouped_cpu.items():
                        mem_val = cpu_df[cpu_df["service"] == svc]["mem_percent"].mean()
                        cpu_rows.append({
                            "profile": profile_key,
                            "scenario": scenario_key,
                            "users": SCENARIO_USERS.get(scenario_key, 0),
                            "rep": rep,
                            "service": svc,
                            "cpu_percent": cpu_val,
                            "mem_percent": mem_val,
                        })
            except Exception as exc:
                print(f"[WARN] Erro ao ler {cpu_path}: {exc}")

        for _, row in df.iterrows():
            name = str(row.get("Name", "")).strip()
            req_count = float(row.get("Request Count", 0))
            fail_count = float(row.get("Failure Count", 0))
            fail_rate = (fail_count / req_count * 100.0) if req_count > 0 else 0.0
            avg_rt = float(row.get("Average Response Time", 0.0))
            p95_rt = float(row.get("95%", 0.0))
            rps = float(row.get("Requests/s", 0.0))

            record = {
                "profile": profile_key,
                "scenario": scenario_key,
                "users": SCENARIO_USERS.get(scenario_key, 0),
                "rep": rep,
                "operation": name,
                "avg_response_ms": avg_rt,
                "p95_response_ms": p95_rt,
                "throughput_rps": rps,
                "total_requests": req_count,
                "failure_count": fail_count,
                "failure_rate_pct": fail_rate,
                "cpu_api_gateway_pct": cpu_by_service.get("api-gateway", 0.0),
                "cpu_customers_service_pct": cpu_by_service.get("customers-service", 0.0),
                "cpu_vets_service_pct": cpu_by_service.get("vets-service", 0.0),
            }

            if name == "Aggregated":
                overall_rows.append(record)
            else:
                operation_rows.append(record)

    return pd.DataFrame(overall_rows), pd.DataFrame(operation_rows), pd.DataFrame(cpu_rows)


def generate_charts(summary_overall: pd.DataFrame, summary_ops: pd.DataFrame, summary_cpu: pd.DataFrame, charts_dir: Path):
    # Gera os graficos comparativos em results/charts/
    charts_dir.mkdir(parents=True, exist_ok=True)
    profiles = ["Perfil1_Leitura", "Perfil2_Escrita"]
    colors = {"Perfil1_Leitura": "#1f77b4", "Perfil2_Escrita": "#d62728"}

    # Grafico 1: Tempo medio de resposta e P95
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(SCENARIO_ORDER))
    width = 0.35

    for idx, (metric, title, ylabel) in enumerate([
        ("avg_response_ms", "Tempo Medio de Resposta por Cenario", "Tempo Medio de Resposta (ms)"),
        ("p95_response_ms", "Tempo de Resposta P95 por Cenario", "Tempo de Resposta P95 (ms)"),
    ]):
        ax = axes[idx]
        for i, prof in enumerate(profiles):
            sub = summary_overall[summary_overall["profile"] == prof].set_index("scenario").reindex(SCENARIO_ORDER)
            vals = sub[metric].fillna(0).values
            bars = ax.bar(x + (i - 0.5) * width, vals, width, label=PROFILE_LABELS[prof], color=colors[prof])
            ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=8)
        ax.set_title(title, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER])
        ax.set_ylabel(ylabel)
        ax.legend()

    plt.tight_layout()
    plt.savefig(charts_dir / "01_tempo_resposta_medio_e_p95.png")
    plt.close()

    # Grafico 2: Vazao e total de requisicoes
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for idx, (metric, title, ylabel, fmt) in enumerate([
        ("throughput_rps", "Vazao Media (Throughput) por Cenario", "Vazao (req/s)", "%.1f"),
        ("total_requests", "Total Medio de Requisicoes (5 min uteis)", "Total de Requisicoes", "%.0f"),
    ]):
        ax = axes[idx]
        for i, prof in enumerate(profiles):
            sub = summary_overall[summary_overall["profile"] == prof].set_index("scenario").reindex(SCENARIO_ORDER)
            vals = sub[metric].fillna(0).values
            bars = ax.bar(x + (i - 0.5) * width, vals, width, label=PROFILE_LABELS[prof], color=colors[prof])
            ax.bar_label(bars, fmt=fmt, padding=3, fontsize=8)
        ax.set_title(title, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER])
        ax.set_ylabel(ylabel)
        ax.legend()

    plt.tight_layout()
    plt.savefig(charts_dir / "02_vazao_e_total_requisicoes.png")
    plt.close()

    # Grafico 3: Tempo medio por operacao
    if not summary_ops.empty:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
        operations = ["GET /owners", "GET /owners/{id}", "GET /vets", "POST /owners"]
        op_colors = ["#2b5c8f", "#388e3c", "#f57c00", "#c62828"]

        for idx, prof in enumerate(profiles):
            ax = axes[idx]
            sub_prof = summary_ops[summary_ops["profile"] == prof]
            bar_w = 0.2
            for j, op in enumerate(operations):
                sub_op = sub_prof[sub_prof["operation"] == op].set_index("scenario").reindex(SCENARIO_ORDER)
                vals = sub_op["avg_response_ms"].fillna(0).values
                bars = ax.bar(x + (j - 1.5) * bar_w, vals, bar_w, label=op, color=op_colors[j])
                ax.bar_label(bars, fmt="%.0f", padding=2, fontsize=7)
            ax.set_title(f"Tempo Medio por Operacao - {PROFILE_LABELS[prof]}", fontweight="bold")
            ax.set_xticks(x)
            ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER])
            ax.set_ylabel("Tempo Medio de Resposta (ms)")
            ax.legend()

        plt.tight_layout()
        plt.savefig(charts_dir / "03_degradacao_por_operacao.png")
        plt.close()

    # Grafico 4: Utilizacao de CPU por servico
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    svc_metrics = [
        ("cpu_api_gateway_pct", "api-gateway", "#1f77b4"),
        ("cpu_customers_service_pct", "customers-service", "#ff7f0e"),
        ("cpu_vets_service_pct", "vets-service", "#2ca02c"),
    ]
    for idx, prof in enumerate(profiles):
        ax = axes[idx]
        sub = summary_overall[summary_overall["profile"] == prof].set_index("scenario").reindex(SCENARIO_ORDER)
        bar_w = 0.25
        for j, (col, label, color) in enumerate(svc_metrics):
            vals = sub[col].fillna(0).values
            bars = ax.bar(x + (j - 1) * bar_w, vals, bar_w, label=label, color=color)
            ax.bar_label(bars, fmt="%.1f%%", padding=2, fontsize=8)
        ax.set_title(f"Utilizacao de CPU por Servico - {PROFILE_LABELS[prof]}", fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER])
        ax.set_ylabel("Utilizacao Media de CPU (%)")
        ax.legend()

    plt.tight_layout()
    plt.savefig(charts_dir / "04_utilizacao_cpu_servicos.png")
    plt.close()

    # Grafico 5: Taxa de falhas
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, prof in enumerate(profiles):
        sub = summary_overall[summary_overall["profile"] == prof].set_index("scenario").reindex(SCENARIO_ORDER)
        vals = sub["failure_rate_pct"].fillna(0).values
        bars = ax.bar(x + (i - 0.5) * width, vals, width, label=PROFILE_LABELS[prof], color=colors[prof])
        ax.bar_label(bars, fmt="%.2f%%", padding=3, fontsize=8)
    ax.set_title("Taxa Media de Falhas (%) por Cenario e Perfil", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER])
    ax.set_ylabel("Taxa de Falhas (%)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(charts_dir / "05_taxa_de_falhas.png")
    plt.close()


def write_markdown_tables(summary_overall: pd.DataFrame, summary_ops: pd.DataFrame, out_path: Path):
    # Exporta as tabelas consolidadas em formato Markdown
    lines = ["# Tabelas Consolidadas dos Experimentos (Media das Repeticoes)\n"]
    lines.append("## 1. Metricas Globais por Cenario e Perfil\n")
    lines.append("| Perfil | Cenario | Usuarios | Tempo Medio (ms) | P95 (ms) | Vazao (req/s) | Total Req. | Taxa de Falhas (%) | CPU `api-gateway` (%) | CPU `customers-service` (%) | CPU `vets-service` (%) |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for _, row in summary_overall.iterrows():
        p_label = PROFILE_LABELS.get(row["profile"], row["profile"])
        s_label = SCENARIO_LABELS.get(row["scenario"], row["scenario"])
        lines.append(
            f"| {p_label} | {s_label} | {int(row['users'])} | "
            f"{row['avg_response_ms']:.2f} | {row['p95_response_ms']:.2f} | "
            f"{row['throughput_rps']:.2f} | {row['total_requests']:.0f} | "
            f"{row['failure_rate_pct']:.2f}% | {row['cpu_api_gateway_pct']:.2f}% | "
            f"{row['cpu_customers_service_pct']:.2f}% | {row['cpu_vets_service_pct']:.2f}% |"
        )

    if not summary_ops.empty:
        lines.append("\n## 2. Metricas por Operacao (Endpoint)\n")
        lines.append("| Perfil | Cenario | Operacao | Tempo Medio (ms) | P95 (ms) | Vazao (req/s) | Total Req. | Taxa de Falhas (%) |")
        lines.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")
        for _, row in summary_ops.iterrows():
            p_label = PROFILE_LABELS.get(row["profile"], row["profile"])
            s_label = SCENARIO_LABELS.get(row["scenario"], row["scenario"])
            lines.append(
                f"| {p_label} | {s_label} | `{row['operation']}` | "
                f"{row['avg_response_ms']:.2f} | {row['p95_response_ms']:.2f} | "
                f"{row['throughput_rps']:.2f} | {row['total_requests']:.0f} | "
                f"{row['failure_rate_pct']:.2f}% |"
            )

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    raw_dir = Path("results/raw")
    results_dir = Path("results")
    charts_dir = results_dir / "charts"
    results_dir.mkdir(parents=True, exist_ok=True)

    overall_df, ops_df, cpu_df = load_raw_results(raw_dir)
    if overall_df.empty:
        print("Nenhum arquivo de resultado encontrado em results/raw/.")
        return

    summary_overall = (
        overall_df.groupby(["profile", "scenario", "users"], as_index=False)
        .agg({
            "avg_response_ms": "mean",
            "p95_response_ms": "mean",
            "throughput_rps": "mean",
            "total_requests": "mean",
            "failure_count": "mean",
            "failure_rate_pct": "mean",
            "cpu_api_gateway_pct": "mean",
            "cpu_customers_service_pct": "mean",
            "cpu_vets_service_pct": "mean",
        })
    )

    summary_ops = pd.DataFrame()
    if not ops_df.empty:
        summary_ops = (
            ops_df.groupby(["profile", "scenario", "users", "operation"], as_index=False)
            .agg({
                "avg_response_ms": "mean",
                "p95_response_ms": "mean",
                "throughput_rps": "mean",
                "total_requests": "mean",
                "failure_count": "mean",
                "failure_rate_pct": "mean",
            })
        )

    summary_cpu = pd.DataFrame()
    if not cpu_df.empty:
        summary_cpu = (
            cpu_df.groupby(["profile", "scenario", "users", "service"], as_index=False)
            .agg({
                "cpu_percent": "mean",
                "mem_percent": "mean",
            })
        )

    summary_overall.to_csv(results_dir / "summary_overall.csv", index=False)
    if not summary_ops.empty:
        summary_ops.to_csv(results_dir / "summary_operations.csv", index=False)
    if not summary_cpu.empty:
        summary_cpu.to_csv(results_dir / "summary_cpu.csv", index=False)

    write_markdown_tables(summary_overall, summary_ops, results_dir / "tables.md")
    generate_charts(summary_overall, summary_ops, summary_cpu, charts_dir)
    print("Tabelas e graficos gerados em results/ e results/charts/.")


if __name__ == "__main__":
    main()
