"""
Licence: Apache 2.0
Author: Martin A. Koch, PhD (martinandreaskoch@catsalut.cat)
(c) 2026, Servei CAtalà de la Salut. CatSalut
"""

gitHubList = [
	'https://github.com/openEHR/CKM-mirror/archive/refs/heads/master.zip',    # International CKM
	'https://github.com/AppertaFoundation/apperta-uk-ckm-mirror/archive/refs/heads/master.zip',
	'https://github.com/CKMCatSalut/CKM-mirror/archive/refs/heads/master.zip',
	'https://github.com/Arketyper-no/ckm/archive/refs/heads/master.zip',
	'https://github.com/openEHR-de/CKM-mirror/archive/refs/heads/master.zip'
]


from lxml import etree
import shutil
import time
import zipfile
import json
import math
import requests
import os
import pandas as pd


#download for github zip files
def fetch_zip_file(url, zipFileName):
	# Try to get the ZIP file
	try:
		response = requests.get(url)
	except OSError:
		print('No connection to the server!')
		return None

	# check if the request is succesful
	if response.status_code == 200:
		# Save dataset to file
		print('Status 200, OK')
		open(zipFileName, 'wb').write(response.content)
	else:
		print('ZIP file request not successful!.')
		return None


def remove_folder_with_retries(folder, retries=5, delay=1):
	for attempt in range(retries):
		try:
			shutil.rmtree(folder)
			print(f"Deleted folder: {folder}")
			return
		except PermissionError as e:
			print(f"Attempt {attempt+1}: PermissionError - {e}")
			time.sleep(delay)
		except FileNotFoundError:
			print(f"Folder not found: {folder}")
			return
	print(f"Failed to delete folder after {retries} attempts.")

def extract_zip_to_flat_temp(zip_path):
	# Create the "temp" directory if it doesn't exist
	temp_dir = "temp"
	os.makedirs(temp_dir, exist_ok=True)

	# Open the zip file
	with zipfile.ZipFile(zip_path, 'r') as zip_ref:
		# Iterate through each file in the zip
		for member in zip_ref.namelist():
			# Get the file name only, ignoring any subfolder structure
			filename = os.path.basename(member)

			# Only extract if it's a file (skip directories)
			if filename:
				# Define the full path for the extracted file
				dest_path = os.path.join(temp_dir, filename)

				# Open the file from the zip and write it to the "temp" folder
				with zip_ref.open(member) as source, open(dest_path, "wb") as target:
					target.write(source.read())

	print(f"All files extracted to '{temp_dir}' without subfolders.")

def list_files(dir,ext):
	#temp_dir = "temp"
	# Get a list of all files in the "temp" folder
	file_list = [f for f in os.listdir(dir) if f.endswith((ext))]
	return file_list

def parse_template(filepath):
	tree = etree.parse(filepath)
	root = tree.getroot()
	ns = {'t': root.nsmap.get(None, '')}  # handle default namespace

	archetype_set = set()
	containment_edges = []

	# Recursively walk the definition tree
	def walk(element, parent_archetype=None):
		# Look for archetype_id in the element
		arch_id_el = element.find('.//archetype_id/value', ns)
		# or via attribute, depending on format
		if arch_id_el is not None:
			arch_id = arch_id_el.text
		else:
			arch_id = element.attrib.get('archetype_id', None)

		if arch_id:
			archetype_set.add(arch_id)
			if parent_archetype:
				containment_edges.append((parent_archetype, arch_id))
			parent_archetype = arch_id

		for child in element:
			walk(child, parent_archetype)

	walk(root)

	#template_id = root.findtext('.//template_id/value', default=filepath)
	template_id = filepath[5:-4]

	myDict = []

	for ce in containment_edges:
		node = {
		'source': ce[0],
		'target': ce[1],
		'template': template_id,
		'URL': template_sources[template_id]
		}
		myDict.append(node)


	return myDict

# Usage
remove_folder_with_retries('temp')

template_sources = {}

# df_sources = pd.DataFrame(columns=['source', 'template_id', 'parent_archetype', 'child_archetype']);

for gitHubURL in gitHubList:
	zipFileName = 'TempZipFile.zip'
	fetch_zip_file(gitHubURL, zipFileName)
	with zipfile.ZipFile(zipFileName, 'r') as zf:
		oet_names = [
			os.path.splitext(os.path.basename(name))[0]
			for name in zf.namelist()
			if name.endswith('.oet')
		]
	for oet in oet_names:
		template_sources[oet] = gitHubURL
	extract_zip_to_flat_temp(zipFileName)
	#delete zip file
	os.remove(zipFileName)
	print('Done!')


#extract_zip_to_flat_temp(zipFileName)
#list all files
total_template_number = 0
fileList = list_files('temp','.oet')
total_template_number += len(fileList)
connection_dictionary = []

for file in fileList:
	filepath = 'temp/'+ file
	connection_dictionary += parse_template(filepath)

df_sources = pd.DataFrame(connection_dictionary)
df_sources = df_sources.rename(columns={"source": "parent_archetype",
				   "target": "child_archetype",
				   "template": "template_id",
				   "URL": "source"
				   })

df_sources.to_excel('source_data.xlsx', index=False)

archetypeList = []
conn_pairs = []
#get all pairings
for conn in connection_dictionary:
	conn_pairs.append((conn['source'],conn['target']))
	archetypeList.append(conn['source'])
	archetypeList.append(conn['target'])

conn_pairs_set = list(set(conn_pairs))
archetypeList = list(sorted(set(archetypeList)))

frequency = []

for cp in conn_pairs_set:
	count = conn_pairs.count(cp)
	normalized_count = math.ceil(count/total_template_number*100)
	frequ_text = ''
	limit = 10
	if count <= limit:
		frequ_text = 'sometimes'
	if count > limit:
		frequ_text = 'often'

	max_line_width = 75
	line_width = math.ceil(max_line_width*normalized_count/100)

	frequency.append((cp[0], cp[1], count, frequ_text, line_width))


Nodes = []
Edges = []

for origin_archetype in archetypeList:
	used_in_templates = df_sources.loc[(df_sources["parent_archetype"] == origin_archetype) | (df_sources["child_archetype"] == origin_archetype),"template_id"].unique().tolist()

	# Create a human-readable evaluation of the archetype
	info_text = ''

	# ── Header ──
	info_text += '<h3 style="margin:0 0 4px 0; color:#fff;">' + origin_archetype + '</h3>'
	info_text += '<hr style="border:none; height:1px; background:rgba(255,255,255,0.06); margin:8px 0 16px 0;">'

	# Get all pairs where the archetype contains another archetype
	a = [t for t in frequency if t[0] == origin_archetype]
	a_sometimes = [t for t in a if t[3] == 'sometimes']
	a_often = [t for t in a if t[3] == 'often']

	# Get all pairs where this archetype was included by another archetype
	b = [t for t in frequency if t[1] == origin_archetype]
	b_sometimes = [t for t in b if t[3] == 'sometimes']
	b_often = [t for t in b if t[3] == 'often']

	# ── Archetype Inclusions (collapsible) ──
	has_inclusions = a_often or a_sometimes or b_often or b_sometimes

	if has_inclusions:
		info_text += '<div class="collapsible-section">'
		info_text += '<button class="collapsible-toggle" onclick="this.parentElement.classList.toggle(\'collapsed\')">'
		info_text += '<span class="material-icons-round toggle-icon">expand_more</span>'
		info_text += '<span>Archetype Inclusions</span>'
		info_text += '</button>'
		info_text += '<div class="collapsible-content">'

		# ── Includes ──
		if a_often or a_sometimes:
			info_text += '<h4 style="margin:8px 0 10px 0; color:#8888a4; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Includes</h4>'

			if a_often:
				info_text += '<div style="margin-bottom:12px;">'
				info_text += '<span style="display:inline-block; background:rgba(0,212,170,0.12); color:#00d4aa; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; margin-bottom:6px;">OFTEN</span>'
				info_text += '<ul style="list-style:none; padding:0; margin:4px 0 0 0;">'
				for a_o in a_often:
					info_text += '<li style="padding:4px 0 4px 12px; border-left:2px solid #00d4aa; margin-bottom:4px; font-size:12px; cursor:pointer; transition:color .15s;" '
					info_text += 'onmouseover="this.style.color=\'#00d4aa\'" onmouseout="this.style.color=\'inherit\'" '
					info_text += 'onclick="if(typeof focusNode===\'function\')focusNode(\'' + a_o[1].replace("'", "\\'") + '\')">'
					info_text += a_o[1] + '</li>'
				info_text += '</ul></div>'

			if a_sometimes:
				info_text += '<div style="margin-bottom:12px;">'
				info_text += '<span style="display:inline-block; background:rgba(108,99,255,0.12); color:#6c63ff; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; margin-bottom:6px;">SOMETIMES</span>'
				info_text += '<ul style="list-style:none; padding:0; margin:4px 0 0 0;">'
				for a_s in a_sometimes:
					info_text += '<li style="padding:4px 0 4px 12px; border-left:2px solid #6c63ff; margin-bottom:4px; font-size:12px; cursor:pointer; transition:color .15s;" '
					info_text += 'onmouseover="this.style.color=\'#6c63ff\'" onmouseout="this.style.color=\'inherit\'" '
					info_text += 'onclick="if(typeof focusNode===\'function\')focusNode(\'' + a_s[1].replace("'", "\\'") + '\')">'
					info_text += a_s[1] + '</li>'
				info_text += '</ul></div>'

		# ── Included by ──
		if b_often or b_sometimes:
			info_text += '<h4 style="margin:12px 0 10px 0; color:#8888a4; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Included by</h4>'

			if b_often:
				info_text += '<div style="margin-bottom:12px;">'
				info_text += '<span style="display:inline-block; background:rgba(0,212,170,0.12); color:#00d4aa; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; margin-bottom:6px;">OFTEN</span>'
				info_text += '<ul style="list-style:none; padding:0; margin:4px 0 0 0;">'
				for b_o in b_often:
					info_text += '<li style="padding:4px 0 4px 12px; border-left:2px solid #00d4aa; margin-bottom:4px; font-size:12px; cursor:pointer; transition:color .15s;" '
					info_text += 'onmouseover="this.style.color=\'#00d4aa\'" onmouseout="this.style.color=\'inherit\'" '
					info_text += 'onclick="if(typeof focusNode===\'function\')focusNode(\'' + b_o[0].replace("'", "\\'") + '\')">'
					info_text += b_o[0] + '</li>'
				info_text += '</ul></div>'

			if b_sometimes:
				info_text += '<div style="margin-bottom:12px;">'
				info_text += '<span style="display:inline-block; background:rgba(108,99,255,0.12); color:#6c63ff; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; margin-bottom:6px;">SOMETIMES</span>'
				info_text += '<ul style="list-style:none; padding:0; margin:4px 0 0 0;">'
				for b_s in b_sometimes:
					info_text += '<li style="padding:4px 0 4px 12px; border-left:2px solid #6c63ff; margin-bottom:4px; font-size:12px; cursor:pointer; transition:color .15s;" '
					info_text += 'onmouseover="this.style.color=\'#6c63ff\'" onmouseout="this.style.color=\'inherit\'" '
					info_text += 'onclick="if(typeof focusNode===\'function\')focusNode(\'' + b_s[0].replace("'", "\\'") + '\')">'
					info_text += b_s[0] + '</li>'
				info_text += '</ul></div>'

		info_text += '</div></div>'  # close collapsible-content and collapsible-section

	# ── Empty inclusions state ──
	if not has_inclusions:
	   info_text += '<p style="color:#8888a4; font-size:12px; font-style:italic;">No inclusion relationships found for this archetype.</p>'

	# ── Templates (collapsible) ──
	# Assumes `node_templates` is a list of template names for this archetype
	if used_in_templates and len(used_in_templates) > 0:
		sorted_templates = sorted(used_in_templates)
		info_text += '<div class="collapsible-section" style="margin-top:8px;">'
		info_text += '<button class="collapsible-toggle" onclick="this.parentElement.classList.toggle(\'collapsed\')">'
		info_text += '<span class="material-icons-round toggle-icon">expand_more</span>'
		info_text += '<span>Templates (' + str(len(sorted_templates)) + ')</span>'
		info_text += '</button>'
		info_text += '<div class="collapsible-content">'
		info_text += '<ul style="list-style:none; padding:0; margin:8px 0 0 0;">'
		for tmpl in sorted_templates:
			info_text += '<li style="padding:5px 0 5px 12px; border-left:2px solid #f5a623; margin-bottom:3px; font-size:12px; cursor:pointer; transition:color .15s;" '
			info_text += 'onmouseover="this.style.color=\'#f5a623\'" onmouseout="this.style.color=\'inherit\'" '
			info_text += 'onclick="if(typeof selectTemplate===\'function\')selectTemplate(\'' + tmpl.replace("'", "\\'") + '\')">'
			info_text += tmpl + '</li>'
		info_text += '</ul>'
		info_text += '</div></div>'

	title_val = info_text


	Nodes.append(
					{
						'id': origin_archetype,
						'label': origin_archetype,
						'title': origin_archetype,
						'templates': used_in_templates,
						'info' : title_val,
						'shape': "dot",
						'size': 18,
						'color': {
							'background': "#6c63ff",
							'border': "#8a83ff",
							'highlight': {
								'background': "#00d4aa",
								'border': "#00f0c0"
							},
							'hover': {
								'background': "#8a83ff",
								'border': "#a09aff"
							}
						},
						'font': {
							'color': "#cccce0",
							'size': 12
						}
					}
					)

	# how many times did this archetype include other archetypes

	for target_archetype in archetypeList:
		for f in frequency:
			if f[0] == origin_archetype and f[1] == target_archetype:

				edges_used_in_templates = df_sources.loc[(df_sources["parent_archetype"] == origin_archetype) & (df_sources["child_archetype"] == target_archetype),"template_id"].unique().tolist()



				Edges.append(
					{
						'from': target_archetype,
						'to': origin_archetype,
						'templates': edges_used_in_templates,
						'arrows': "to",
						'width': f[2],
						'color': {
							'color': "rgba(108,99,255,0.45)",
							'highlight': "#00d4aa",
							'hover': "rgba(108,99,255,0.7)"
						},
						'smooth': {
							'type': "curvedCW",
							'roundness': 0.15
						}
					}
				)

nodeText = ''
nodeText += "nodes = new vis.DataSet(" + json.dumps(Nodes, ensure_ascii=False) + ");\n"
nodeText += "edges = new vis.DataSet(" + json.dumps(Edges, ensure_ascii=False) + ");\n"
f = open("dataset.js", "w", encoding='utf-8')
f.write(nodeText)
f.close()
