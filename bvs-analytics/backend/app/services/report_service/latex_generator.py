import tempfile
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Any

class settings: COMPILE_RETRY = 3
# from ...core.config import settings

def generate_report(begin_date: date | None = None, end_date: date | None = None, region: str | None = None, extended: bool = False, image_dir: str = '') -> str:
    data = {}

    # Create temporary directory for thread-safe operation
    with tempfile.TemporaryDirectory() as temp_dir:
        # prepare temporary latex directory
        temp_dir_path = Path(temp_dir)
        (temp_dir_path / "sections").mkdir()
        
        # Copy images to temporary directory
        temp_image_path = temp_dir_path / "images"
        if image_dir:
            shutil.copytree(Path(image_dir), temp_image_path, dirs_exist_ok=True)

        # Generate latex content to files
        (temp_dir_path / "preamble.sty").write_text(generate_preamble(), encoding='utf-8')
        (temp_dir_path / "main.tex").write_text(generate_main_tex(begin_date, end_date, region, extended, data), encoding='utf-8')
        (temp_dir_path / "sections" / "metrics.tex").write_text(generate_metrics_tex(data, [img_file.name.split('.')[0] for img_file in temp_image_path.iterdir()]), encoding='utf-8')
        if extended:
            (temp_dir_path / "sections" / "flights.tex").write_text(generate_flights_tex(data, extended), encoding='utf-8')
        
        # Compile LaTeX
        retry_counter = 0
        while retry_counter < settings.COMPILE_RETRY and not compile_latex(temp_dir_path):
            retry_counter += 1
            print(f"Retry counter: {retry_counter}")
        
        if retry_counter == settings.COMPILE_RETRY:
            print("Error: report generation retry limit exceeded")
            return ''

        # Copy final PDF to current directory with proper name
        region_safe = (region.replace(' ', '_') if region else "all_regions").replace('/', '_')
        time_segment = 'full'
        if begin_date:
            if end_date:
                time_segment = f'{begin_date.strftime('%d.%m.%Y')}-{end_date.strftime('%d.%m.%Y')}'
            else:
                time_segment = f'since_{begin_date.strftime('%d.%m.%Y')}'
        elif end_date:
            time_segment = f'before_{end_date.strftime('%d.%m.%Y')}'

        output_filename = f"report_{region_safe}_{time_segment}.pdf"
        final_pdf = temp_dir_path / "main.pdf"
        if not final_pdf.exists():
            print("Error: report PDF wasn't generated")
            return ''
        shutil.copy2(final_pdf, output_filename)
        print(f"Report generated successfully: {output_filename}")
        return output_filename
        


def generate_main_tex(begin_date: date | None, end_date: date | None, region: str | None, extended: bool, data: Dict[str, Any]) -> str:
    time_segment = 'полный'
    if begin_date:
        if end_date:
            time_segment = f'{begin_date.strftime('%d.%m.%Y')}-{end_date.strftime('%d.%m.%Y')}'
        else:
            time_segment = f'с {begin_date.strftime('%d.%m.%Y')}'
    elif end_date:
        time_segment = f'до {end_date.strftime('%d.%m.%Y')}'

    return fr"""\documentclass[a4paper,11pt]{{report}}
\usepackage{{preamble}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage[utf8]{{inputenc}}
\usepackage[T2A]{{fontenc}}
\usepackage[russian]{{babel}}

\title{{{"Отчёт" if region else "Общий отчёт"} о статистике полётов БПЛА, {region + ", " if region else ""}{time_segment}}}
\author{{Автоматически сгенерированный отчёт}}
\date{{\today}}

\begin{{document}}

\begin{{titlepage}}
    \centering
    \vspace*{{2cm}}
    
    {{\Huge \textbf{{\title}}}}
    
    \vspace{{3cm}}
    
    \begin{{tabular}}{{ll}}
        \textbf{{Регион:}} & {region if region else 'все'} \\
        \textbf{{Период:}} & {begin_date.strftime('%d.%m.%Y')} -- {end_date.strftime('%d.%m.%Y')} \\
    \end{{tabular}}
    
    \vfill
\end{{titlepage}}

\input{{sections/metrics.tex}}

{(r'\section{Список полётов}' + '\n' + r'\input{sections/flights.tex}') if extended else ''}

\end{{document}}"""

def generate_preamble():
    return r"""\ProvidesPackage{preamble}

\usepackage[utf8]{inputenc}
\usepackage[T2A]{fontenc}
\usepackage[russian]{babel}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{geometry}
\geometry{a4paper, margin=2.5cm}

% For tables
\usepackage{array}
\usepackage{booktabs}

% For advanced graphics
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{width=0.9\textwidth, compat=1.9}
\usepackage{float}
"""

def generate_metrics_tex(data: Dict[str, Any], images : list[str] = []) -> str:
    graph_title_mapping = {
        'peak_load' : 'Пиковая нагрузка: максимальное число полётов за час',
        'daily_dynamics' : 'Среднесуточная динамика полётов'
    }

    graphics = ""
    for image in images:
        if image in graph_title_mapping.keys():
            graphics += fr"""
\begin{{figure}}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{{{{images/{image}.png}}}}
    \caption{{{graph_title_mapping[image]}}}
\end{{figure}}
"""

    return fr"""\section{{Основные метрики}}

\begin{{itemize}}
    \item \textbf{{Общее количество полётов:}} {data['total_flights']}
    \item \textbf{{Средняя длительность полёта:}} {data['avg_duration']} минут
    \item \textbf{{Пиковая нагрузка:}} {data['peak_load']} полётов в час
    \item \textbf{{Изменение за месяц:}} {data['monthly_change']}\%
    \item \textbf{{Плотность полётов:}} {data['flight_density']} на 1000 км²
    \item \textbf{{Дней без полётов:}} {data['zero_days']}
\end{{itemize}}

\subsection{{Топ-10 регионов по количеству полётов}}

\begin{{enumerate}}
    {chr(10).join(f'    \\item {{ {region} }}' for region in data['top_regions'])}
\end{{enumerate}}
""" + ("\\section{Графики}\n" + graphics if graphics else "")


def generate_flights_tex(data: Dict[str, Any], extended: bool) -> str:
    if not extended:
        return "% Flight list section not included"
    
    return r"""\subsection{Детальный список полётов}

\begin{table}[H]
\centering
\begin{tabular}{|l|l|l|l|}
\hline
\textbf{Время начала} & \textbf{Длительность (мин)} & \textbf{Регион} & \textbf{Тип БПЛА} \\
\hline
01.10.2023 08:30 & 45 & Москва & DJI Mavic 3 \\
01.10.2023 09:15 & 32 & Московская область & DJI Air 2S \\
01.10.2023 10:45 & 56 & Санкт-Петербург & Autel Evo II \\
\hline
\end{tabular}
\caption{Пример данных полётов (замените на реальные данные)}
\end{table}"""


def compile_latex(temp_dir_path: Path) -> bool:
    """Compile LaTeX document using pdflatex"""
    try:
        # Run pdflatex twice to resolve references
        for i in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', 'main.tex'],
                cwd=temp_dir_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                print(f"LaTeX compilation error (run {i+1}):")
                print(result.stderr)
                return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("LaTeX compilation timed out")
        return False
    except Exception as e:
        print(f"Error during LaTeX compilation: {e}")
        return False

if __name__ == "__main__":
    generate_report(date(1984, 1, 1), date(1985, 1, 1))