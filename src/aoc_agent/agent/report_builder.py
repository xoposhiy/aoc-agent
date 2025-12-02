from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

from rich import print


class ReportBuilder:
    def __init__(self, run_dir: str = "data/run", reports_dir: str = "data/reports"):
        self.run_dir = run_dir
        self.reports_dir = reports_dir

    def build_report(self) -> str:
        """
        Scans the run directory for metadata.json files, aggregates them,
        and generates an HTML report.
        Returns the path to the generated report.
        """
        all_metadata = self._collect_metadata()
        if not all_metadata:
            print("[yellow]No metadata found to generate report.[/yellow]")
            return ""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs(self.reports_dir, exist_ok=True)
        report_path = os.path.join(self.reports_dir, f"report_all_{timestamp}.html")
        report_path_default = os.path.join(self.reports_dir, f"report.html")

        html_content = self._generate_html(all_metadata, timestamp)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        with open(report_path_default, "w", encoding="utf-8") as f:
            f.write(html_content)


        print(f"[bold green]Report generated successfully:[/bold green] {report_path}")
        return report_path

    def _collect_metadata(self) -> List[Dict[str, Any]]:
        results = []
        if not os.path.exists(self.run_dir):
            return results

        for entry in os.listdir(self.run_dir):
            full_path = os.path.join(self.run_dir, entry)
            if os.path.isdir(full_path):
                meta_file = os.path.join(full_path, "metadata.json")
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            results.append(data)
                    except Exception as e:
                        print(f"[red]Error reading {meta_file}: {e}[/red]")
        return results

    def _get_color_style(self, value: float, min_val: float, max_val: float, low_is_good: bool = True) -> str:
        if max_val <= min_val:
            return ""

        # normalize to 0..1 using sqrt for non-linear scaling
        v = max(0, value)
        mn = max(0, min_val)
        mx = max(0, max_val)
        
        denom = math.sqrt(mx) - math.sqrt(mn)
        if denom == 0:
            return ""

        ratio = (math.sqrt(v) - math.sqrt(mn)) / denom
        
        # If low is good (e.g. errors), 0 -> Green, 1 -> Red
        if not low_is_good:
            ratio = 1 - ratio
            
        # Color Gradient:
        # Good (Low): Light Green #ccffcc (204, 255, 204)
        # Bad (High): Light Red #ffcccc (255, 204, 204)
        
        start_rgb = (204, 255, 204) # Green
        end_rgb = (255, 204, 204)   # Red
        
        r = int(start_rgb[0] + ratio * (end_rgb[0] - start_rgb[0]))
        g = int(start_rgb[1] + ratio * (end_rgb[1] - start_rgb[1]))
        b = int(start_rgb[2] + ratio * (end_rgb[2] - start_rgb[2]))
        
        return f'style="background-color: rgb({r}, {g}, {b})"'

    def _generate_html(self, results: List[Dict[str, Any]], timestamp: str) -> str:
        # --- New: Pairwise Comparison Section ---
        pairwise_html = self._generate_pairwise_section(results)
        charts_html = self._generate_charts_section(results)
        model_charts_html = self._generate_model_comparison_charts(results)

        # Group by Year -> Day -> Lang -> Model
        # Structure: grouped[year][(day, lang, model)] = list of runs
        grouped: Dict[int, Dict[tuple, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        
        for r in results:
            year = r.get('year', 'Unknown')
            key = (r.get('day', 0), r.get('lang', 'unknown'), r.get('model', 'unknown'))
            grouped[year][key].append(r)

        years = sorted(grouped.keys())

        html = """
        <!DOCTYPE html>
        <html>
        <head>
        <title>AoC Agent Report (All Runs)</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h1, h2, h3 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f1f1f1; }
            .summary { font-weight: bold; margin-bottom: 10px; color: #555; }
            .success { color: green; font-weight: bold; }
            .failure { color: red; font-weight: bold; }
            .year-section { margin-top: 40px; border-top: 2px solid #eee; padding-top: 20px; }
            .matrix-header { font-weight: bold; background-color: #e0e0e0; }
            .self-cell { background-color: #eee; color: #aaa; }
            .pairwise-table td { text-align: center; }
            .pairwise-table th { min-width: 80px; }
            .pairwise-table { width: auto; }
            .better { color: green; font-weight: bold; }
            .worse { color: red; font-weight: bold; }
            .metric-good { color: green; font-weight: bold; }
            .metric-bad { color: red; font-weight: bold; }
            .metric-neutral { color: #777; }
            .sub-label { font-size: 0.8em; color: #888; display: block; }
        </style>
        </head>
        <body>
        <h1>AoC Agent Report</h1>
        <p>Generated at: """ + timestamp + """</p>
        
        """ + pairwise_html + """
        
        """ + charts_html + """
        
        """ + model_charts_html + """
        
        """
        
        for year in years:
            html += f"<div class='year-section'><h2>Year {year}</h2>"
            
            # Stats for year
            # ... (we could add yearly aggregation here) ...
            
            html += "<table><thead><tr>"
            html += "<th>Day</th><th>Lang</th><th>Model</th><th>N Runs</th>"
            html += "<th>P1 Solved</th><th>P2 Solved</th>"
            html += "<th>Avg Dur (s)</th><th>Min Dur (s)</th>"
            html += "<th>Avg Tok</th><th>Min Tok</th>"
            html += "<th>Avg Fric</th><th>Min Fric</th>"
            html += "</tr></thead><tbody>"
            
            # Sort keys by day desc
            year_keys = sorted(grouped[year].keys(), key=lambda x: (x[0], x[1], x[2]), reverse=True)
            
            # Prepare rows for coloring
            rows_stats = []
            vals_min_tokens = []
            vals_avg_friction = []
            vals_min_friction = []
            
            for day, lang, model in year_keys:
                runs = grouped[year][(day, lang, model)]
                n = len(runs)
                
                p1_solved_count = sum(1 for r in runs if r.get('part1_solved'))
                p2_solved_count = sum(1 for r in runs if r.get('part2_solved'))
                
                # Calculate stats
                durs = [r.get('part12_duration', 0) for r in runs]
                avg_dur = sum(durs) / n
                min_dur = min(durs)
                
                toks = [r.get('part12_output_tokens', 0) for r in runs]
                avg_tok = sum(toks) / n
                min_tok = min(toks)
                
                # Friction: Incorrect attempts + run code errors
                frictions = [
                    r.get('part1_incorrect', 0) + 
                    r.get('part2_incorrect', 0) + 
                    r.get('part1_run_code_errors', 0) + 
                    r.get('part2_run_code_errors', 0)
                    for r in runs
                ]
                avg_fric = sum(frictions) / n
                min_fric = min(frictions)
                
                n_success = sum(1 for r in runs if r.get('part2_solved'))
                
                rows_stats.append({
                    'day': day,
                    'lang': lang,
                    'model': model,
                    'n': n,
                    'p1_solved_count': p1_solved_count,
                    'p2_solved_count': p2_solved_count,
                    'p1_class': 'success' if p1_solved_count == n else ('failure' if p1_solved_count == 0 else ''),
                    'p2_class': 'success' if p2_solved_count == n else ('failure' if p2_solved_count == 0 else ''),
                    'avg_dur': avg_dur,
                    'min_dur': min_dur,
                    'avg_tokens': avg_tok,
                    'min_tokens': min_tok,
                    'avg_friction': avg_fric,
                    'min_friction': min_fric,
                    'n_success': n_success
                })
                
                if n_success > 0:
                    vals_min_tokens.append(min_tok)
                    vals_avg_friction.append(avg_fric)
                    vals_min_friction.append(min_fric)

            # Determine ranges for coloring
            range_min_tokens = (min(vals_min_tokens, default=0), max(vals_min_tokens, default=0))
            range_avg_friction = (min(vals_avg_friction, default=0), max(vals_avg_friction, default=0))
            range_min_friction = (min(vals_min_friction, default=0), max(vals_min_friction, default=0))

            # 3. Render Rows
            for rs in rows_stats:
                style_min_tokens = self._get_color_style(rs['min_tokens'], *range_min_tokens)
                style_avg_friction = self._get_color_style(rs['avg_friction'], *range_avg_friction) if rs['n_success'] > 0 else ""
                style_min_friction = self._get_color_style(rs['min_friction'], *range_min_friction) if rs['n_success'] > 0 else ""

                html += f"<tr>"
                html += f"<td>{rs['day']}</td>"
                html += f"<td>{rs['lang']}</td>"
                html += f"<td>{rs['model']}</td>"
                html += f"<td>{rs['n']}</td>"
                html += f"<td class='{rs['p1_class']}'>{rs['p1_solved_count']}/{rs['n']} ({rs['p1_solved_count']/rs['n']*100:.0f}%)</td>"
                html += f"<td class='{rs['p2_class']}'>{rs['p2_solved_count']}/{rs['n']} ({rs['p2_solved_count']/rs['n']*100:.0f}%)</td>"
                html += f"<td>{rs['avg_dur']:.2f}</td>"
                html += f"<td>{rs['min_dur']:.2f}</td>"
                html += f"<td>{rs['avg_tokens']:.0f}</td>"
                html += f"<td {style_min_tokens}>{rs['min_tokens']:.0f}</td>"
                
                if rs['n_success'] > 0:
                    html += f"<td {style_avg_friction}>{rs['avg_friction']:.1f}</td>"
                    html += f"<td {style_min_friction}>{rs['min_friction']:.1f}</td>"
                else:
                    html += "<td>-</td><td>-</td>"
                
                html += f"</tr>"
            
            html += "</tbody></table></div>"

        html += "</body></html>"
        return html

    def _aggregate_stats(self, results: List[Dict[str, Any]]) -> tuple[Dict[tuple, Dict[str, Dict[str, float]]], set]:
        task_map: Dict[tuple, Dict[str, Dict[str, float]]] = defaultdict(dict)
        all_langs = set()
        grouped_runs: Dict[tuple, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        
        for r in results:
            if not r.get('part2_solved', False):
                continue
                
            y, d = r.get('year'), r.get('day')
            l = r.get('lang')
            m = r.get('model', 'unknown')
            if y is None or d is None or l is None:
                continue
                
            grouped_runs[(y, d, m)][l].append(r)
            all_langs.add(l)

        for key, lang_runs in grouped_runs.items():
            for lang, runs in lang_runs.items():
                avg_dur = sum(r.get('part12_duration', 0) for r in runs) / len(runs)
                avg_tok = sum(r.get('part12_output_tokens', 0) for r in runs) / len(runs)
                
                friction_sum = sum(
                    r.get('part1_incorrect', 0) + 
                    r.get('part2_incorrect', 0) + 
                    r.get('part1_run_code_errors', 0) + 
                    r.get('part2_run_code_errors', 0)
                    for r in runs
                )
                avg_fric = friction_sum / len(runs)
                
                task_map[key][lang] = {'dur': avg_dur, 'tok': avg_tok, 'fric': avg_fric}
                
        return task_map, all_langs

    def _generate_charts_section(self, results: List[Dict[str, Any]]) -> str:
        task_map, all_langs = self._aggregate_stats(results)
        sorted_langs = sorted(list(all_langs))
        if len(sorted_langs) < 2:
            return ""
            
        html = "<div class='year-section'><h2>Token Usage Comparison (XY Charts)</h2>"
        html += "<p class='summary'>X-axis: Language 1 Avg Tokens, Y-axis: Language 2 Avg Tokens. Each point is a task (Year, Day). Colors represent models.</p>"
        
        pairs = []
        for i in range(len(sorted_langs)):
            for j in range(i + 1, len(sorted_langs)):
                pairs.append((sorted_langs[i], sorted_langs[j]))
        
        html += "<div style='display: flex; flex-wrap: wrap; gap: 20px;'>"
        
        chart_js_code = ""
        # Palette
        colors = [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)'
        ]
        
        has_charts = False
        for lang1, lang2 in pairs:
            chart_id = f"chart_{lang1}_{lang2}".replace(".", "_").replace("#", "Sharp")
            datasets = defaultdict(list)
            max_val = 0.0
            
            for key, langs_data in task_map.items():
                year, day, model = key
                if lang1 in langs_data and lang2 in langs_data:
                    stat1 = langs_data[lang1]
                    stat2 = langs_data[lang2]
                    pt = {
                        'x': stat1['tok'],
                        'y': stat2['tok'],
                        'year': year,
                        'day': day
                    }
                    datasets[model].append(pt)
                    if pt['x'] > max_val: max_val = pt['x']
                    if pt['y'] > max_val: max_val = pt['y']
            
            if not datasets:
                continue
            
            has_charts = True
            html += f"<div style='width: 45%; min-width: 500px; max-width: 500px;'><canvas id='{chart_id}'></canvas></div>"
            
            chart_data_sets = []
            
            # Add diagonal y=x line
            chart_data_sets.append({
                'type': 'line',
                'label': 'y=x',
                'data': [{'x': 0, 'y': 0}, {'x': max_val, 'y': max_val}],
                'borderColor': 'rgba(150, 150, 150, 0.5)',
                'borderWidth': 2,
                'borderDash': [5, 5],
                'pointRadius': 0,
                'fill': False
            })
            
            for idx, (model, points) in enumerate(datasets.items()):
                color = colors[idx % len(colors)]
                ds = {
                    'label': model,
                    'data': points,
                    'backgroundColor': color,
                    'borderColor': color,
                    'pointRadius': 5,
                }
                chart_data_sets.append(ds)
            
            chart_js_code += f"""
            new Chart(document.getElementById('{chart_id}'), {{
                type: 'scatter',
                data: {{
                    datasets: {json.dumps(chart_data_sets)}
                }},
                options: {{
                    responsive: true,
                    aspectRatio: 1,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '{lang1} vs {lang2} (Tokens)'
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    let pt = context.raw;
                                    return context.dataset.label + ': (' + pt.x.toFixed(1) + ', ' + pt.y.toFixed(1) + ') [' + pt.year + ' Day ' + pt.day + ']';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            type: 'linear',
                            position: 'bottom',
                            title: {{
                                display: true,
                                text: '{lang1} Avg Tokens'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: '{lang2} Avg Tokens'
                            }}
                        }}
                    }}
                }}
            }});
            """
            
        html += "</div>"
        if has_charts:
            html += f"<script>{chart_js_code}</script>"
        else:
            html += "<p>No overlapping data for charts.</p>"
            
        html += "</div>"
        return html

    def _generate_model_comparison_charts(self, results: List[Dict[str, Any]]) -> str:
        # 1. Aggregate data by (Year, Day, Lang) -> {model: stats}
        grouped_data = defaultdict(lambda: defaultdict(list))
        
        target_models = ['gpt-5', 'gemini-3-pro-preview', 'claude-opus-4-5']
        all_langs = set()

        for r in results:
            if not r.get('part2_solved', False):
                continue
            
            y, d = r.get('year'), r.get('day')
            l = r.get('lang')
            m = r.get('model', 'unknown')
            
            if y is None or d is None or l is None:
                continue
            
            if m in target_models:
                grouped_data[(y, d, l)][m].append(r)
                all_langs.add(l)

        # Compute averages
        # model_task_map[(year, day, lang)][model] = {tok: float}
        model_task_map = defaultdict(dict)
        
        for key, model_runs in grouped_data.items():
            for m, runs in model_runs.items():
                avg_tok = sum(r.get('part12_output_tokens', 0) for r in runs) / len(runs)
                model_task_map[key][m] = {'tok': avg_tok}

        # 2. Generate Pairs
        pairs = []
        for i in range(len(target_models)):
            for j in range(i + 1, len(target_models)):
                pairs.append((target_models[i], target_models[j]))

        html = "<div class='year-section'><h2>Model Token Usage Comparison (XY Charts)</h2>"
        html += "<p class='summary'>X-axis: Model 1 Avg Tokens, Y-axis: Model 2 Avg Tokens. Each point is a task (Year, Day) per Language. Colors represent Languages.</p>"
        html += "<div style='display: flex; flex-wrap: wrap; gap: 20px;'>"

        chart_js_code = ""
        
        sorted_langs = sorted(list(all_langs))
        base_colors = [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)',
            'rgba(83, 102, 255, 0.7)',
        ]
        lang_colors = {l: base_colors[i % len(base_colors)] for i, l in enumerate(sorted_langs)}

        has_charts = False
        
        for m1, m2 in pairs:
             datasets = defaultdict(list) # key is Language
             max_val = 0.0
             
             for key, models_data in model_task_map.items():
                 year, day, lang = key
                 if m1 in models_data and m2 in models_data:
                     val1 = models_data[m1]['tok']
                     val2 = models_data[m2]['tok']
                     pt = {
                         'x': val1,
                         'y': val2,
                         'year': year,
                         'day': day
                     }
                     datasets[lang].append(pt)
                     max_val = max(max_val, val1, val2)
             
             if not datasets:
                 continue

             has_charts = True
             chart_id = f"chart_model_{m1}_{m2}".replace("-", "_").replace(".", "_")
             
             html += f"<div style='width: 45%; min-width: 500px; max-width: 500px;'><canvas id='{chart_id}'></canvas></div>"
             
             chart_data_sets = []
             # Diagonal line
             chart_data_sets.append({
                'type': 'line',
                'label': 'y=x',
                'data': [{'x': 0, 'y': 0}, {'x': max_val, 'y': max_val}],
                'borderColor': 'rgba(150, 150, 150, 0.5)',
                'borderWidth': 2,
                'borderDash': [5, 5],
                'pointRadius': 0,
                'fill': False
            })

             for lang, points in datasets.items():
                 color = lang_colors.get(lang, 'rgba(0,0,0,0.5)')
                 ds = {
                    'label': lang,
                    'data': points,
                    'backgroundColor': color,
                    'borderColor': color,
                    'pointRadius': 5,
                 }
                 chart_data_sets.append(ds)
            
             chart_js_code += f"""
            new Chart(document.getElementById('{chart_id}'), {{
                type: 'scatter',
                data: {{
                    datasets: {json.dumps(chart_data_sets)}
                }},
                options: {{
                    responsive: true,
                    aspectRatio: 1,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '{m1} vs {m2} (Tokens)'
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    let pt = context.raw;
                                    return context.dataset.label + ': (' + pt.x.toFixed(1) + ', ' + pt.y.toFixed(1) + ') [' + pt.year + ' Day ' + pt.day + ']';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            type: 'linear',
                            position: 'bottom',
                            title: {{
                                display: true,
                                text: '{m1} Avg Tokens'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: '{m2} Avg Tokens'
                            }}
                        }}
                    }}
                }}
            }});
            """

        html += "</div>"
        if has_charts:
             html += f"<script>{chart_js_code}</script>"
        else:
             html += "<p>No overlapping data for selected models.</p>"

        return html

    def _generate_pairwise_section(self, results: List[Dict[str, Any]]) -> str:
        """
        Generates a pairwise comparison matrix for languages based on overlapping tasks.
        Methodology:
          - Compare Language A vs Language B only on tasks (Year, Day) where BOTH have successful solutions.
          - Metric = Geometric Mean of Ratios (Metric_A / Metric_B) across all common tasks.
          - Ratios < 1.0 indicate Language A is better (faster/smaller).
        """
        
        # 1. Aggregation: Calculate average stats per (Year, Day, Lang) for SUCCESSFUL runs
        task_map, all_langs = self._aggregate_stats(results)

        sorted_langs = sorted(list(all_langs))
        if len(sorted_langs) < 2:
            return ""

        # 2. Build Matrix
        html = "<div class='year-section'><h2>Language Head-to-Head Comparison</h2>"
        html += "<p class='summary'>Comparison on overlapping tasks (where both languages solved Part 2).</p>"
        html += "<table class='pairwise-table'><thead><tr><th class='matrix-header'>Row vs Col</th>"
        for l in sorted_langs:
            html += f"<th class='matrix-header'>{l}</th>"
        html += "</tr></thead><tbody>"

        for lang_a in sorted_langs:
            html += f"<tr><td class='matrix-header'>{lang_a}</td>"
            for lang_b in sorted_langs:
                if lang_a == lang_b:
                    html += "<td class='self-cell'>—</td>"
                    continue

                # Compare A vs B
                ratios_dur = []
                ratios_tok = []
                diffs_fric = []
                common_count = 0

                for key, langs_data in task_map.items():
                    if lang_a in langs_data and lang_b in langs_data:
                        stat_a = langs_data[lang_a]
                        stat_b = langs_data[lang_b]
                        
                        # Ratio: A / B. If A is faster, ratio < 1.
                        if stat_b['dur'] > 0:
                            ratios_dur.append(stat_a['dur'] / stat_b['dur'])
                        if stat_b['tok'] > 0:
                            ratios_tok.append(stat_a['tok'] / stat_b['tok'])
                        
                        # Friction Difference: A - B. If A has less friction, diff < 0.
                        diffs_fric.append(stat_a['fric'] - stat_b['fric'])
                        
                        common_count += 1

                if common_count == 0:
                    html += "<td><span class='metric-neutral'>N/A</span></td>"
                else:
                    # Geometric Mean for Ratios
                    geo_dur = math.exp(sum(math.log(x) for x in ratios_dur) / len(ratios_dur)) if ratios_dur else 1.0
                    geo_tok = math.exp(sum(math.log(x) for x in ratios_tok) / len(ratios_tok)) if ratios_tok else 1.0
                    
                    # Arithmetic Mean for Friction Difference
                    avg_diff_fric = sum(diffs_fric) / len(diffs_fric) if diffs_fric else 0.0
                    
                    def fmt_cls(val):
                        if val < 0.95: return "metric-good"
                        if val > 1.05: return "metric-bad"
                        return "metric-neutral"

                    def fmt_fric(val):
                        if val < -0.1: return "metric-good"
                        if val > 0.1: return "metric-bad"
                        return "metric-neutral"

                    html += "<td class='matrix-cell'>"
                    html += f"<div class='{fmt_cls(geo_dur)}'>Time: {geo_dur:.2f}x</div>"
                    html += f"<div class='{fmt_cls(geo_tok)}'>Tokens: {geo_tok:.2f}x</div>"
                    
                    sign = "+" if avg_diff_fric > 0 else ""
                    html += f"<div class='{fmt_fric(avg_diff_fric)}'>Friction: {sign}{avg_diff_fric:.1f}</div>"
                    
                    html += f"<span class='sub-label'>({common_count} tasks)</span>"
                    html += "</td>"

            html += "</tr>"
        
        html += "</tbody></table></div>"
        return html
