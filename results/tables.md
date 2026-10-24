# Tabelas Consolidadas dos Experimentos (Media das Repeticoes)

## 1. Metricas Globais por Cenario e Perfil

| Perfil | Cenario | Usuarios | Tempo Medio (ms) | P95 (ms) | Vazao (req/s) | Total Req. | Taxa de Falhas (%) | CPU `api-gateway` (%) | CPU `customers-service` (%) | CPU `vets-service` (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Perfil 1 - Leitura | A - Leve (30 usu.) | 30 | 420.98 | 1207.20 | 21.13 | 6293 | 88.55% | 20.58% | 168.37% | 5.85% |
| Perfil 1 - Leitura | B - Moderado (80 usu.) | 80 | 417.96 | 1024.20 | 62.06 | 18517 | 95.96% | 35.90% | 178.53% | 2.64% |
| Perfil 1 - Leitura | C - Elevado (150 usu.) | 150 | 222.89 | 851.10 | 125.40 | 37438 | 98.23% | 59.13% | 150.95% | 1.69% |
| Perfil 2 - Escrita | A - Leve (30 usu.) | 30 | 449.03 | 1225.70 | 20.68 | 6138 | 86.38% | 10.31% | 163.12% | 1.93% |
| Perfil 2 - Escrita | B - Moderado (80 usu.) | 80 | 205.84 | 81.50 | 66.02 | 19702 | 98.56% | 28.80% | 138.67% | 1.30% |
| Perfil 2 - Escrita | C - Elevado (150 usu.) | 150 | 177.73 | 137.30 | 125.91 | 37567 | 99.30% | 57.92% | 139.15% | 1.44% |

## 2. Metricas por Operacao (Endpoint)

| Perfil | Cenario | Operacao | Tempo Medio (ms) | P95 (ms) | Vazao (req/s) | Total Req. | Taxa de Falhas (%) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Perfil 1 - Leitura | A - Leve (30 usu.) | `GET /owners` | 557.72 | 6201.30 | 9.53 | 2836 | 89.72% |
| Perfil 1 - Leitura | A - Leve (30 usu.) | `GET /owners/{id}` | 414.88 | 2142.70 | 7.42 | 2211 | 88.70% |
| Perfil 1 - Leitura | A - Leve (30 usu.) | `GET /vets` | 20.59 | 47.00 | 3.12 | 928 | 84.52% |
| Perfil 1 - Leitura | A - Leve (30 usu.) | `POST /owners` | 426.29 | 3132.40 | 1.07 | 318 | 88.94% |
| Perfil 1 - Leitura | B - Moderado (80 usu.) | `GET /owners` | 532.42 | 1023.80 | 27.87 | 8314 | 96.74% |
| Perfil 1 - Leitura | B - Moderado (80 usu.) | `GET /owners/{id}` | 435.83 | 913.20 | 21.80 | 6504 | 95.85% |
| Perfil 1 - Leitura | B - Moderado (80 usu.) | `GET /vets` | 16.33 | 37.30 | 9.32 | 2780 | 93.99% |
| Perfil 1 - Leitura | B - Moderado (80 usu.) | `POST /owners` | 498.15 | 980.90 | 3.08 | 919 | 95.66% |
| Perfil 1 - Leitura | C - Elevado (150 usu.) | `GET /owners` | 269.29 | 899.30 | 56.31 | 16809 | 98.51% |
| Perfil 1 - Leitura | C - Elevado (150 usu.) | `GET /owners/{id}` | 238.05 | 796.90 | 43.99 | 13133 | 98.32% |
| Perfil 1 - Leitura | C - Elevado (150 usu.) | `GET /vets` | 29.43 | 103.90 | 18.83 | 5622 | 97.08% |
| Perfil 1 - Leitura | C - Elevado (150 usu.) | `POST /owners` | 273.56 | 831.30 | 6.28 | 1874 | 98.36% |
| Perfil 2 - Escrita | A - Leve (30 usu.) | `GET /owners` | 905.36 | 9640.00 | 4.12 | 1222 | 89.34% |
| Perfil 2 - Escrita | A - Leve (30 usu.) | `GET /owners/{id}` | 417.33 | 1110.70 | 4.17 | 1236 | 86.57% |
| Perfil 2 - Escrita | A - Leve (30 usu.) | `GET /vets` | 10.95 | 24.20 | 4.18 | 1240 | 82.93% |
| Perfil 2 - Escrita | A - Leve (30 usu.) | `POST /owners` | 458.63 | 1101.30 | 8.22 | 2440 | 86.57% |
| Perfil 2 - Escrita | B - Moderado (80 usu.) | `GET /owners` | 296.13 | 478.90 | 13.15 | 3923 | 99.72% |
| Perfil 2 - Escrita | B - Moderado (80 usu.) | `GET /owners/{id}` | 211.90 | 48.70 | 13.30 | 3970 | 98.88% |
| Perfil 2 - Escrita | B - Moderado (80 usu.) | `GET /vets` | 15.06 | 42.60 | 13.21 | 3943 | 96.99% |
| Perfil 2 - Escrita | B - Moderado (80 usu.) | `POST /owners` | 253.43 | 94.20 | 26.36 | 7866 | 98.60% |
| Perfil 2 - Escrita | C - Elevado (150 usu.) | `GET /owners` | 222.16 | 109.30 | 25.19 | 7517 | 99.95% |
| Perfil 2 - Escrita | C - Elevado (150 usu.) | `GET /owners/{id}` | 181.52 | 111.50 | 25.24 | 7532 | 99.50% |
| Perfil 2 - Escrita | C - Elevado (150 usu.) | `GET /vets` | 28.44 | 95.90 | 25.23 | 7529 | 98.05% |
| Perfil 2 - Escrita | C - Elevado (150 usu.) | `POST /owners` | 228.57 | 159.70 | 50.24 | 14990 | 99.49% |
