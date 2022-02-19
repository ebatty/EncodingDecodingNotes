# Inspired by Neuromatch generate_book.py https://github.com/NeuromatchAcademy/nmaci
import os

import yaml
from jinja2 import Template
import traceback
import json
from bs4 import BeautifulSoup

REPO = os.environ.get("NMA_REPO", "course-content")

def main():

    # Get list of notebooks
    with open('_toc.yml') as fh:
        materials = yaml.load(fh, Loader=yaml.FullLoader)

    notebook_list = []
    for i_part in range(len(materials['parts'])):
        for i_chapter in range(len(materials['parts'][i_part]['chapters'])):
            notebook_list.append( materials['parts'][0]['chapters'][i_chapter]['file'])

    # Process all notebooks
    for notebook_file_path in notebook_list:
        pre_process_notebook(notebook_file_path)


def pre_process_notebook(file_path):

    with open(file_path, encoding="utf-8") as read_notebook:
        content = json.load(read_notebook)
    pre_processed_content = open_in_colab_new_tab(content)
    pre_processed_content = change_video_widths(pre_processed_content)
    pre_processed_content = link_hidden_cells(pre_processed_content)
    pre_processed_content = make_stop_and_thinks(pre_processed_content)

    with open(file_path, "w", encoding="utf-8") as write_notebook:
        json.dump(pre_processed_content, write_notebook, indent=1, ensure_ascii=False)

def make_stop_and_thinks(content):
    cells = content['cells']
    updated_cells = cells.copy()

    i_updated_cell = 0
    for i_cell, cell in enumerate(cells):
        if cell['source'][0].startswith("**Stop and think!**"):
            question = cell['source'][0]
            for jj in range(1, len(cell['source'])):
                    answer = ''.join(cell['source'][2:])

            updated_cells[i_cell]['source'] = [f'```{{admonition}} {question}',
                ':class: tip, dropdown\n',
                f'{answer}']
            
    content['cells'] = updated_cells
    return content

def open_in_colab_new_tab(content):
    cells = content['cells']
    parsed_html = BeautifulSoup(cells[0]['source'][0], "html.parser")
    for anchor in parsed_html.findAll('a'):
        # Open in new tab
        anchor['target'] = '_blank'
    cells[0]['source'][0] = str(parsed_html)
    return content

def link_hidden_cells(content):
    cells = content['cells']
    updated_cells = cells.copy()

    i_updated_cell = 0
    for i_cell, cell in enumerate(cells):
        updated_cell = updated_cells[i_updated_cell]
        if "source" not in cell:
            continue
        source = cell['source'][0]

        if source.startswith("#") and cell['cell_type'] == 'markdown':
            header_level = source.count('#')
        elif source.startswith("---") and cell['cell_type'] == 'markdown':
            if len(cell['source']) > 1 and cell['source'][1].startswith("#") and cell['cell_type'] == 'markdown':
                header_level = cell['source'][1].count('#')

        if '@title' in source or '@markdown' in source:
            if 'metadata' not in cell:
                updated_cell['metadata'] = {}
            if 'tags' not in cell['metadata']:
                updated_cell['metadata']['tags'] = []

            # Check if cell is video one
            if 'YouTubeVideo' in ''.join(cell['source']) or 'IFrame' in ''.join(cell['source']):
                if "remove-input" not in cell['metadata']['tags']:
                    updated_cell['metadata']['tags'].append("remove-input")
            else:
                if "hide-input" not in cell['metadata']['tags']:
                    updated_cell['metadata']['tags'].append("hide-input")

            # If header is lost, create one in markdown
            if '@title' in source:

                if source.split('@title')[1] != '':
                    header_cell = {
                        'cell_type': 'markdown',
                        'metadata': {},
                        'source': ['#'*(header_level + 1) + ' ' + source.split('@title')[1]]}
                    updated_cells.insert(i_updated_cell, header_cell)
                    i_updated_cell += 1

            strings_with_markdown = [(i, string) for i, string in enumerate(cell['source']) if '@markdown' in string]
            if len(strings_with_markdown) == 1:
                i = strings_with_markdown[0][0]
                if cell['source'][i].split('@markdown')[1] != '':
                    header_cell = {
                        'cell_type': 'markdown',
                        'metadata': {},
                        'source': [cell['source'][i].split('@markdown')[1]]}
                    updated_cells.insert(i_updated_cell, header_cell)
                    i_updated_cell += 1

        i_updated_cell += 1

    content['cells'] = updated_cells
    return content

def change_video_widths(content):

    for cell in content['cells']:
        if 'YouTubeVideo' in ''.join(cell['source']):

            for ind in range(len(cell['source'])):
                # Change sizes
                cell['source'][ind] = cell['source'][ind].replace('854', '730')
                cell['source'][ind] = cell['source'][ind].replace('480', '410')

        # Put slides in ipywidget so they don't overlap margin
        if len(cell['source']) > 1 and 'IFrame' in cell['source'][1]:
            slide_link = ''.join(cell['source']).split('"')[1].split(", width")[0][:-1]
            cell['source'] = ['# @markdown\n',
                              'from IPython.display import IFrame\n',
                              'out = widgets.Output()\n',
                              'with out:\n',
                              f'    display(IFrame(src=f"{slide_link}", width=730, height=410))\n',
                              'display(out)']
    return content

if __name__ == '__main__':
    main()
