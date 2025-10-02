import tempfile
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Any
from sqlalchemy.orm import Session

from .report_preparation import prepare_data
from ..core.config import settings

def generate_report(db : Session, begin_date: str | None = None, end_date: str | None = None, region: str | None = None, extended: bool = False) -> str:
    # Create temporary directory for thread-safe operation
    with tempfile.TemporaryDirectory() as temp_dir:
        # prepare temporary latex directory
        temp_dir_path = Path(temp_dir)
        (temp_dir_path / "sections").mkdir()
        
        # Get data
        temp_image_path = temp_dir_path / "images"
        temp_image_path.mkdir()
        data = prepare_data(db, temp_image_path, begin_date, end_date)

        # Generate latex content to files
        (temp_dir_path / "preamble.sty").write_text(generate_preamble(), encoding='utf-8')
        (temp_dir_path / "main.tex").write_text(generate_main_tex(begin_date, end_date, region, extended), encoding='utf-8')
        (temp_dir_path / "sections" / "metrics.tex").write_text(generate_metrics_tex(data, [img_file.name for img_file in temp_image_path.iterdir()]), encoding='utf-8')
        # if extended:
        #     (temp_dir_path / "sections" / "flights.tex").write_text(generate_flights_tex(flight_data, extended), encoding='utf-8')
        
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
                time_segment = f'{begin_date}-{end_date}'
            else:
                time_segment = f'since_{begin_date}'
        elif end_date:
            time_segment = f'before_{end_date}'

        output_filename = f"report_{region_safe}_{time_segment}.pdf"
        final_pdf = temp_dir_path / "main.pdf"
        if not final_pdf.exists():
            print("Error: report PDF wasn't generated")
            return ''
        shutil.copy2(final_pdf, output_filename)
        print(f"Report generated successfully: {output_filename}")
        return output_filename
        


def generate_main_tex(begin_date: str | None, end_date: str | None, region: str | None, extended: bool) -> str:
    time_segment = 'полный'
    if begin_date:
        if end_date:
            time_segment = f'{begin_date}-{end_date}'
        else:
            time_segment = f'с {begin_date}'
    elif end_date:
        time_segment = f'до {end_date}'

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
    
    {{\Huge \textbf{{Статистика полётов БВС}}}}
    
    \vspace{{3cm}}
    
    \begin{{tabular}}{{ll}}
%        \textbf{{Регион:}} & {region if region else 'все'} \\
        \textbf{{Период:}} & {begin_date} -- {end_date} \\
    \end{{tabular}}
    
    \vfill
\end{{titlepage}}

\input{{sections/metrics.tex}}

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
        "topByCount.png" : "Топ-15 регионов по количеству полётов",
        "topByDuration.png" : "Топ-15 регионов по суммарной длительности полётов",
        "byHour.png" : "Распределение полётов по времени суток",
        "byWeekday.png" : "Полёты по дням недели",
        "byMonth.png" : "Полёты по месяцам",
        "byType.png" : "Распределение полётов по типам БПЛА"
    }

    graphics = ""
    for image in images:
        if image in graph_title_mapping.keys():
            graphics += fr"""
\begin{{figure}}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{{{{images/{image}}}}}
    \caption{{{graph_title_mapping[image]}}}
\end{{figure}}
"""
    top_regions = sorted(data['regions'].values(), key=lambda x : x.get("flights"), reverse=True)[:15]
    top_regions_str = '\n'.join(f'    \\item {{ {region.get("name")} }}' for region in top_regions)
    return fr"""\section{{Основные метрики}}
\begin{{itemize}}
    \item \textbf{{Общее количество полетов:}} {data['flights']}
    \item \textbf{{Суммарная длительность полетов:}} {data['duration']} минут
    \item \textbf{{Средняя длительность полета:}} {data['avg_duration']} минут
    \item \textbf{{Число уникальных типов БПЛА:}} {sum(1 for _ in data['types'])}
    \item \textbf{{Число операторов:}} {sum(1 for _ in data['operators'])}
\end{{itemize}}

\subsection{{Топ-15 регионов по количеству полётов}}

\begin{{enumerate}}
    {top_regions_str}
\end{{enumerate}}
""" + (("\\section{Графики}\n" + graphics) if graphics else "")


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