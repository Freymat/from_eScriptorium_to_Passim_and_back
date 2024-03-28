from config import *
from packages import *
#----get basic informations-------------------------------------------------------

def get_serverinfo(servername,serverconnections):
  serverconnection=search_any('servername', servername, serverconnections)[0]
  print('switching to ',servername)
  headers = serverconnection['headers']
  headersbrief = serverconnection['headersbrief']
  root_url = serverconnection['root_url']
  return root_url,headers,headersbrief

def loop_through_itempages_and_get_all(base_url,suffix=''):
    result_list=[]
    def get_page(page,result_list):
        data = False
        #url = urljoin(base_url, '?page=%d' % page)
        if suffix=='':
          url = base_url+'?page='+str(page)
        else:
          url = base_url+'?page='+str(page)+'&'+suffix
        res = requests.get(url, headers=headers)
        #print(res.json())
        try:
            data = res.json()
        except json.decoder.JSONDecodeError as e:
            print('exception')
            print(res)
        else:
          if data:
            #print(data)
            result_list += [item for item in data['results']] 
        if data:
          if data['next']:
            get_page(page+1,result_list)
    get_page(1,result_list)
    return(result_list)

def get_pks_of_dict_list(list_of_dictionaries):
    pks =[item['pk'] for item in list_of_dictionaries]
    return pks

def get_sthg_from_dict_list(list_of_dictionaries,sthg):
  return([item[sthg] for item in list_of_dictionaries])

def get_basic_info(doc_pk):
  '''
  input: document ID
  output: 
  nu of parts
  transcription_level_list (list of different transcription levels)
  region_type_list, line_type_list (segmentation ontologies)
  '''
  print('get document segmentation ontology for document: ',doc_pk)
  doc_url = get_documents_url()+str(doc_pk)+'/'
  print(doc_url)
  document_dict=requests.get(url=doc_url,headers=headers).json()
  nu_parts = document_dict['parts_count']
  print('Document:', doc_pk,' with ',nu_parts,' parts')
  region_type_list=document_dict['valid_block_types']
  print('region types:',region_type_list)
  line_type_list=document_dict['valid_line_types']
  print('line types:',line_type_list)
  transcription_level_list=document_dict['transcriptions']
  print('transcription_level_list:',transcription_level_list)
  return nu_parts,transcription_level_list,region_type_list,line_type_list

def get_margin_and_paratext_type_pks(doc_pk):
    region_type_list,line_type_list=get_document_segmentation_ontology(doc_pk)
    for region_type in region_type_list:
        if region_type['name']=='Margin':
            margin_type_pk=region_type['pk']
        elif region_type['name']=='Paratext':
            paratext_type_pk=region_type['pk']
    return margin_type_pk,paratext_type_pk


# get_urls--------------------------------------------------------------------------------------------
def get_documents_url():
  return root_url+'/api/documents/'

def get_specific_doc_url(doc_pk):
  return get_documents_url()+str(doc_pk)+'/'

def get_parts_url(doc_pk):
  return get_specific_doc_url(doc_pk)+'parts/'

def get_specific_part_url(doc_pk,part_pk):
  return get_parts_url(doc_pk)+str(part_pk)+'/'

def get_regions_url(doc_pk,part_pk):
  return get_specific_part_url(doc_pk,part_pk)+'blocks/'

def get_specific_region_url(doc_pk,part_pk,region_pk):
  return get_regions_url(doc_pk,part_pk)+str(region_pk)+'/'

def get_lines_url(doc_pk,part_pk):
  return get_specific_part_url(doc_pk,part_pk)+'lines/'

def get_specific_line_url(doc_pk,part_pk,line_pk):
  return get_lines_url(doc_pk,part_pk)+str(line_pk)+'/'

def get_doc_transcriptions_url(doc_pk):
  return get_specific_doc_url(doc_pk)+'transcriptions/'

def get_part_transcriptions_base_url(doc_pk,part_pk):
  return get_specific_part_url(doc_pk,part_pk)+'transcriptions/'

def get_part_transcriptions_url(doc_pk,part_pk,tr_level):
  return get_specific_part_url(doc_pk,part_pk)+'transcriptions/?transcription='+str(tr_level)+'&'

def get_specific_transcription_url(doc_pk,part_pk,tr_pk):
  return get_part_transcriptions_base_url(doc_pk,part_pk)+str(tr_pk)+'/'

def get_models_url():
  return root_url+'/api/models/'

def get_specific_model_url(model_pk):
  return get_models_url()+str(model_pk)+'/'

#def get_projects_url():
#  return root_url+'/api/projects/'

#def get_linetypes_url():
#  return root_url+'/api/types/lines/'

#def get_regiontypes_url():
#  return root_url+'/api/types/regions/'

#def get_annotationtypes_url():
#  return root_url+'/api/types/annotations/'

#def get_annotationtypes_url():
#  return root_url+'/api/types/part/'


def get_segmentation_url(doc_pk):
  return get_specific_doc_url(doc_pk)+'segment/'

def get_transcribe_url(doc_pk):
  return get_specific_doc_url(doc_pk)+'transcribe/'

  


#---------------create-things-------------------------------------------------------------------------------

def create_new_document(project_name, doc_name, script_pk = "Hebrew", read_direction = "rtl"):
    docs_url = get_documents_url()
    data=json.dumps({"name": doc_name,
                     "main_script": script_pk, 
                     "read_direction": read_direction,
                     "project": project_name,
                     "valid_block_types":
                         [{"pk": 3,"name": "Commentary"},
                         {"pk": 4,"name": "Illustration"},
                         {"pk": 2,"name": "Main"},
                         {"pk": 1,"name": "Title"}]
                     })
    res = requests.post(docs_url, headers = headers, data = data)
    print(res.status_code, res.content)
    jsonResponse = json.loads(res.content.decode('utf-8'))
    doc_pk = jsonResponse['pk']
    return doc_pk

def create_transcription_levels(doc_pk,tr_name): 
    doc_tr_url=get_doc_transcriptions_url(doc_pk)
    transcription_level_list = requests.get(doc_tr_url, headers=headers).json() 
    print('existing transcription levels: ',transcription_level_list) 
    existing_tr_level_names = [tr_level['name'] for tr_level in transcription_level_list]
    if tr_name in existing_tr_level_names:
      print(tr_name,'already exists')
      break_this_code
    else:
      datajson={'name':tr_name} 
      data=json.dumps(datajson) #add check whether tr_level exists
      res=requests.post(doc_tr_url,headers=headers,data=data)
      jsonResponse=json.loads(res.content.decode('utf-8'))
      tr_pk=jsonResponse['pk']
      return tr_pk

def create_region(doc_pk,part_pk,reg_polygon,regiontype_pk = None):
  region_url = get_regions_url(doc_pk,part_pk)
  data = {'document_part':part_pk,'polygon':reg_polygon,'typology':regiontype_pk}
  r = requests.post(url=region_url,headers=headers,data=json.dumps(data))
  return r

def create_line(doc_pk,part_pk,baseline,mask = None, repolygonize = False, linetype_pk = None):
  line_url = get_lines_url(doc_pk,part_pk)
  data = {'document_part':part_pk,'baseline':baseline,'mask' : mask, 'typology':linetype_pk}
  r = requests.post(url=line_url,headers=headers,data=json.dumps(data))
  line_pk = r.json().get('pk')
  if repolygonize:
    repolygonize_line(doc_pk,part_pk,line_pk)
  return r

def bulk_create_lines(doc_pk,part_pk,lines):
  line_url = get_lines_url(doc_pk,part_pk)+'bulk_create/'
  data = {'lines' : lines}
  r = requests.post(url=line_url,headers=headers,data=json.dumps(data))
  return r

"""
def upload_image(doc_pk, dirname, fname):
    parts_url = get_parts_url(doc_pk)
    print(f'parts_url: {parts_url}')
    file = os.path.join(dirname, fname)
    print(f'file: {file}')
    with open(file, 'rb') as fh:
        data = {'name': fname}
        res = requests.post(parts_url, data = data, files = {'image': fh}, headers = headersbrief)
    print(res.status_code, res.content)
    result = res.status_code
    jsonResponse = json.loads(res.content.decode('utf-8'))
    print(jsonResponse)
    part_pk = jsonResponse['pk']
    return part_pk, result
"""

def upload_image(doc_pk, image_path, fname):
    parts_url = get_parts_url(doc_pk)
    with open(image_path, 'rb') as fh:
        data = {'name': fname}
        res = requests.post(parts_url, data = data, files = {'image': fh}, headers = headersbrief)
        res_status_code = res.status_code
        res_content = res.content
        jsonResponse = json.loads(res_content.decode('utf-8'))
        part_pk = jsonResponse['pk']
        return part_pk, res_status_code, res_content

"""

def create_txt_annotation(doc_pk,part_pk,tr_level_pk,start_line_pk,start_offset,end_line_pk,end_offset,annot_type,comments=''):
  url = get_specific_part_url+'annotations/text/'
  # integrate comments
  data = {'taxonomy':annot_type,'transcription': tr_level_pk,'components':[],'start_line':start_line_pk,'start_offset':start_offset,'end_line':end_line_pk,'end_offset':end_offset}
  r = requests.post(url,headers=headers,data = json.dumps(data))
  return r
"""

def merge_lines(doc_pk,part_pk,lines):
  merge_url = get_lines_url(doc_pk,part_pk)+'merge/'
  r = requests.post(merge_url,lines)
  return r

#-DELETE items-------------------------------------------------------------------
def delete_item(delete_url):
  r = requests.delete(delete_url,headers=headers)
  return r

def delete_part(doc_pk,part_pk):
  delete_url = get_specific_part_url(doc_pk,part_pk)
  r = delete_item(delete_url)
  return r

def delete_region(doc_pk,part_pk,region_pk):
  delete_url = get_specific_region_url(doc_pk,part_pk,region_pk)
  r = delete_item(delete_url)
  return r

def delete_all_regions_of_part(doc_pk,part_pk):
  regions = get_all_regions_of_part(doc_pk,part_pk)
  for region in regions:
    delete_region(doc_pk, part_pk, region['pk'])

def delete_line(doc_pk,part_pk,line_pk):
  delete_url = get_specific_line_url(doc_pk,part_pk,line_pk)
  r = delete_item(delete_url)
  return r

def bulk_delete_lines(doc_pk,part_pk,line_pk_list):
  delete_url = get_lines_url(doc_pk,part_pk)+'bulk_delete/'
  bulk_json=json.dumps({'lines': line_pk_list})
  r=requests.post(delete_url,headers=headers,data=bulk_json)
  return r

def delete_all_lines_of_part(doc_pk,part_pk):
  lines = get_all_lines_of_part(doc_pk,part_pk)
  del_lines = [line['pk'] for line in lines]
  r = bulk_delete_lines(doc_pk,part_pk,del_lines)
  return r

def delete_all_lines_of_linetype(doc_pk,part_pk,line_type):
  lines = get_all_lines_of_part(doc_pk,part_pk)
  del_line_pk_list = [line['pk'] for line in lines if line['typology']==line_type]
  r = bulk_delete_lines(doc_pk,part_pk,del_line_pk_list)
  return r

def delete_all_lines_in_region(doc_pk,part_pk,region_pk):
  lines = get_all_lines_of_part(doc_pk,part_pk)
  del_line_pk_list = [line['pk'] for line in lines if line['typology']==region_pk]
  r = bulk_delete_lines(doc_pk,part_pk,del_line_pk_list)
  return r

def delete_all_lines_in_region_types(doc_pk,part_pk,region_type_pk_list):
  if isinstance(region_type_pk_list,int):
    region_type_pk_list = [region_type_pk_list]
  lines = get_all_lines_of_part(doc_pk,part_pk)
  regions = get_all_regions_of_part(doc_pk,part_pk)
  del_line_pk_list = [line['pk'] for line in lines if line['region'] in [region['pk'] for region in regions if region['typology'] in region_type_pk_list]]
  r = bulk_delete_lines(doc_pk,part_pk,del_line_pk_list)
  return r

def delete_all_transcriptions_of_tr_levels_in_linetypes(doc_pk,part_pk,tr_level_pk_list,line_type_pk_list):
  if isinstance(line_type_pk_list,int):
    line_type_pk_list = [line_type_pk_list]
  lines = get_all_lines_of_part(doc_pk,part_pk)
  transcriptions = delete_all_part_transcriptions(doc_pk,part_pk)
  del_transcriptions = [tr for tr in transcriptions if (tr['transcription '] in tr_level_pk_list) and (tr['line'] in [line['pk'] for line in lines if line['typology'] in line_type_pk_list])]
  r = bulk_delete_transcriptions(doc_pk,part_pk,del_transcriptions)
  return r

def delete_all_transcriptions_of_tr_levels_in_regiontypes(doc_pk,part_pk,tr_level_pk_list,region_type_pk_list):
  if isinstance(region_type_pk_list,int):
    region_type_pk_list = [region_type_pk_list]
  if isinstance(tr_level_pk_list,int):
    tr_level_pk_list = [tr_level_pk_list]
  lines = get_all_lines_of_part(doc_pk,part_pk)
  regions = get_all_regions_of_part(doc_pk,part_pk)
  transcriptions = delete_all_part_transcriptions(doc_pk,part_pk)
  del_regions = [region['pk'] for region in regions if region['typology'] in region_type_pk_list]
  del_lines = [line['pk'] for line in lines if line['region'] in del_regions]
  del_transcriptions = [tr for tr in transcriptions if (tr['transcription '] in tr_level_pk_list) and (tr['line'] in del_lines)]
  r = bulk_delete_transcriptions(doc_pk,part_pk,del_transcriptions)
  return r

def bulk_delete_transcriptions(doc_pk,part_pk,transcription_pk_list):
  delete_url = get_part_transcriptions_base_url(doc_pk,part_pk)+'bulk_delete/'
  bulk_json=json.dumps({'lines': transcription_pk_list})
  r=requests.post(delete_url,headers=headers,data=bulk_json)
  return r

def delete_part_transcription(doc_pk,part_pk,tr_level):
  transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
  tr_pks = [tr['pk'] for tr in transcriptions]
  r = bulk_delete_transcriptions(doc_pk,part_pk,tr_pks)
  return r

def delete_all_part_transcriptions(doc_pk,part_pk):
  transcriptions = get_all_page_transcriptions(doc_pk,part_pk)
  tr_pks = [tr['pk'] for tr in transcriptions]
  r = bulk_delete_transcriptions(doc_pk,part_pk,tr_pks)
  return r

def delete_all_part_regions_lines_transcriptions(doc_pk,part_pk):
  delete_all_part_transcriptions(doc_pk,part_pk)
  delete_all_lines_of_part(doc_pk,part_pk)
  delete_all_regions_of_part(doc_pk,part_pk)

#-get-items----------------------------------------------------------------------
def get_item(url):
  return(requests.get(url,headers=headers).json())

def get_all_docs():
  docs_url = get_documents_url()
  return loop_through_itempages_and_get_all(docs_url)

def get_doc(doc_pk):
  doc_url = get_documents_url()
  print(doc_url)
  return(get_item(doc_url))

def get_part(doc_pk,part_pk):
  part_url = get_specific_part_url(doc_pk,part_pk)
  return(get_item(part_url))

def get_region(doc_pk,part_pk,region_pk):
  region_url = get_specific_region_url(doc_pk,part_pk,region_pk)
  return(get_item(region_url))

def get_line(doc_pk,part_pk,line_pk):
  line_url = get_specific_line_url(doc_pk,part_pk,line_pk)
  return(get_item(line_url))

def get_all_parts(doc_pk):
    parts_url = get_parts_url(doc_pk)
    return(loop_through_itempages_and_get_all(parts_url))

def get_all_regions_of_part(doc_pk,part_pk):
    regions_url = get_regions_url(doc_pk,part_pk)
    return(loop_through_itempages_and_get_all(regions_url))

def get_all_lines_of_part(doc_pk,part_pk):
    lines_url = get_lines_url(doc_pk,part_pk)
    return(loop_through_itempages_and_get_all(lines_url))

def page_height_width(doc_pk,part_pk):
  part_dict = get_part(doc_pk,part_pk)
  pagewidth=part_dict['image']['size'][0]
  pageheight=part_dict['image']['size'][1]
  return pageheight,pagewidth

def get_img_from_url(img_url):
  res=requests.get(img_url)
  img = Image.open(io.BytesIO(res.content))
  return(img)

def write_doc_list_from_instance2file(fname='results.tsv'):
  docs = get_all_docs()
  f = open(fname,mode='wt')
  for doc in docs:
    doc_pk=doc['pk']
    doc_name=doc['name']
    doc_img_nu=doc['parts_count']
    f.write(str(doc_pk)+'\t'+doc_name+'\t'+str(doc_img_nu)+'\n')
  f.close()

def get_part_pk_list(doc_pk):
    parts = get_all_parts(doc_pk)
    pks = get_pks_of_dict_list(parts)
    return pks

def get_line_pk_list(doc_pk,part_pk):
    lines = get_all_lines_of_part(doc_pk,part_pk)
    pks = get_pks_of_dict_list(lines)
    return pks
#def get_linetranscription_pk_list(doc_pk, part_pk,tr_pk):
#    tr_url = root_url+'api/documents/'+str(doc_pk)+'/parts/'+str(part_pk)+'/transcriptions/'
#    return(loop_through_itempages(tr_url,'pk','results'))
    
def get_region_pk_list(doc_pk,part_pk):
    regions = get_all_regions_of_part(doc_pk,part_pk)
    pks = get_pks_of_dict_list(regions)
    return pks

def get_inhabited_region_pk_list(doc_pk,part_pk):
    all_lines = get_all_lines_of_part(doc_pk,part_pk)
    inhabited_regions = list(set([line['region'] for line in all_lines]))
    return(inhabited_regions)
  
def get_region_pk_list_of_type(doc_pk,part_pk,region_type):
    regions_url = get_regions_url(doc_pk,part_pk)
    all_regions=get_all_regions_of_part(doc_pk,part_pk)
    regions=[region['pk'] for region in all_regions if region['typology'] == region_type]
    return regions

def get_regions_and_lines(doc_pk,part_pk,tr_level):
  lines_url=get_lines_url(doc_pk,part_pk)
  lines=loop_through_itempages_and_get_all(lines_url)
  regions_url=get_regions_url(doc_pk,part_pk)
  regions=loop_through_itempages_and_get_all(regions_url)
  tr_url = get_part_transcriptions_base_url(doc_pk,part_pk,tr_level)
  tr_suffix = 'transcription='+str(tr_level)
  transcriptions=loop_through_itempages_and_get_all(tr_url,tr_suffix)
  return regions,lines,transcriptions

def get_main_region_pk_list(doc_pk,part_pk):
    regions = get_region_pk_list_of_type(doc_pk,part_pk,2)
    return regions

def get_region_box_list(doc_pk,part_pk):
    regions = get_all_regions_of_part(doc_pk,part_pk)
    return(get_sthg_from_dict_list(regions,'box'))

def get_all_page_transcriptions(doc_pk,part_pk):
    tr_url = get_part_transcriptions_base_url(doc_pk,part_pk)
    return(loop_through_itempages_and_get_all(tr_url))

def get_page_transcription(doc_pk,part_pk,tr_level):
    tr_url = get_part_transcriptions_base_url(doc_pk,part_pk)
    trs =  loop_through_itempages_and_get_all(tr_url)
    return [tr for tr in trs if tr['transcription']==tr_level]

def get_page_transcription_tr_pks(doc_pk,part_pk,tr_level):
    transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
    return(get_sthg_from_dict_list(transcriptions,'pk'))

def get_page_transcription_line_pks(doc_pk,part_pk,tr_level):
    transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
    return(get_sthg_from_dict_list(transcriptions,'line'))

def get_all_lines_of_region(doc_pk,part_pk,region_pk):
    lines_url = get_lines_url(doc_pk,part_pk)
    all_lines = get_all_lines_of_part(doc_pk,part_pk)
    lines = [line for line in all_lines if line['region'] == region_pk]
    return lines

def get_all_line_pks_of_region(doc_pk,part_pk,region_pk):
    lines_url = get_lines_url(doc_pk,part_pk)
    all_lines = get_all_lines_of_part(doc_pk,part_pk)
    line_pks = [line['pk'] for line in all_lines if line['region'] == region_pk]
    return line_pks

def get_document_segmentation_ontology(doc_pk,print_status=False):
    doc_url = get_specific_doc_url(doc_pk)
    document_dict=get_item(doc_url)
    region_type_list=document_dict['valid_block_types']
    line_type_list=document_dict['valid_line_types']
    if print_status:
      print('get document segmentation ontology for document: ',doc_pk)
      print(document_dict)
      for region_type in region_type_list:
          print(region_type)
      for line_type in line_type_list:
          print(line_type)
    return region_type_list,line_type_list

def get_transcription_levels(doc_pk):
    tr_level_url = get_doc_transcriptions_url(doc_pk)
    tr_levels = get_item(tr_level_url)
    return tr_levels

def get_set_of_all_characters_in_transcription_level(doc_pk,part_list,tr_level):
    print('get char set of document for document: ',doc_pk)
    chars = set()
    for n,part_pk in enumerate(part_list):
        if n % 100 == 0:
            print(n,' parts finished')
        transcriptions_this_part=get_page_transcription(doc_pk,part_pk,tr_level)
        for line in transcriptions_this_part:
            chars=chars.union(set(line))    
    chars=list(chars)
    return chars

def get_imgname_list(doc_pk):
    parts = get_all_parts(doc_pk)
    return(get_sthg_from_dict_list(parts,'filename'))

def get_all_models():
  models_url = get_models_url()
  models = loop_through_itempages_and_get_all(models_url)
  simplified_models = [{'pk':model['pk'],'name':model['name'],'file':model['file'],'job':model['job'],'owner':model['owner'],'training':model['training']} for model in models]
  unique_models =  [dict(t) for t in {tuple(d.items()) for d in simplified_models}]
  return(unique_models)

def get_specific_model(model_pk):
  model_url = get_specific_model_url(model_pk)
  return(get_item(model_url))

def get_all_seg_models():
  all_models = get_all_models()
  return [model for model in all_models if model['job'] == 'Segment']

def get_all_trans_models():
  all_models = get_all_models()
  return [model for model in all_models if model['job'] == 'Recognize']

"""
def get_doc_annotation_taxonomies(doc_pk):
  tax_url = get_specific_doc_url(doc_pk)+'taxonomies/annotations/'
  return loop_through_itempages_and_get_all(tax_url)
"""
def get_doc_annotation_components(doc_pk):
  comp_url = get_specific_doc_url(doc_pk)+'taxonomies/components/'
  return loop_through_itempages_and_get_all(comp_url)

def get_doc_txt_annotation_taxonomies(doc_pk):
  text_tax_url = get_specific_doc_url(doc_pk)+'taxonomies/annotations/text/'
  return loop_through_itempages_and_get_all(text_tax_url)

def get_doc_img_annotation_taxonomies(doc_pk):
  img_tax_url = get_specific_doc_url(doc_pk)+'taxonomies/annotations/image/'
  return loop_through_itempages_and_get_all(img_tax_url)

def get_part_txt_annotations(doc_pk,part_pk):
  text_tax_url = get_specific_part_url(doc_pk,part_pk)+'annotations/text/'
  return loop_through_itempages_and_get_all(text_tax_url)

def get_part_img_annotations(doc_pk,part_pk):
  img_tax_url = get_specific_part_url(doc_pk,part_pk)+'annotations/image/'
  return loop_through_itempages_and_get_all(img_tax_url)

def get_specific_part_txt_annotations(doc_pk,part_pk,annot_pk):
  text_tax_url = get_specific_part_url(doc_pk,part_pk)+'annotations/text/'+str(annot_pk)+'/'
  return get_item(text_tax_url)

def get_specific_part_img_annotations(doc_pk,part_pk,annot_pk):
  img_tax_url = get_specific_part_url(doc_pk,part_pk)+'annotations/image/'+str(annot_pk)+'/'
  return get_item(img_tax_url)

def get_all_doc_txt_annotations(doc_pk):
  parts = get_all_parts(doc_pk)
  all_annots = list()
  for part in parts:
    part_pk = part['pk']
    all_annots += get_part_txt_annotations(doc_pk,part_pk)
  return all_annots

def get_all_doc_img_annotations(doc_pk):
  parts = get_all_parts(doc_pk)
  all_annots = list()
  for part in parts:
    part_pk = part['pk']
    all_annots += get_part_img_annotations(doc_pk,part_pk)
  return all_annots

def get_all_doc_annotations(doc_pk):
  parts = get_all_parts(doc_pk)
  all_annots = list()
  for part in parts:
    part_pk = part['pk']
    all_annots += get_part_txt_annotations(doc_pk,part_pk)
    all_annots += get_part_img_annotations(doc_pk,part_pk)
  return all_annots



# modify-basic-data-------------------------------------------------------------------------

def rename_tr_level(doc_pk,tr_level,new_name):
  tr_level_url=get_doc_transcriptions_url(doc_pk)+str(tr_level)+'/'
  rjson=get_item(tr_level_url)
  rjson['name']=new_name
  r=requests.put(tr_level_url,headers=headers,data=json.dumps(rjson))
  return r

def update_item(update_url, item):
  r=requests.put(update_url,headers=headers,data=json.dumps(item))
  return r

def update_part(doc_pk,part_pk,part):
  update_url = get_specific_part_url(doc_pk,part['pk'])
  r = update_item(update_url,part)
  return r

def update_region(doc_pk,part_pk,region):
  update_url = get_specific_region_url(doc_pk,part_pk,region['pk'])
  r = update_item(update_url, region)
  return r

def update_line(doc_pk,part_pk,line):
  update_url = get_specific_line_url(doc_pk,part_pk,line['pk'])
  r = update_item(update_url, line)
  return r

def bulk_update_lines(doc_pk,part_pk,lines):
  bulk_update_url = get_lines_url(doc_pk,part_pk)+'bulk_update/'
  bulk_json=json.dumps({'lines': lines})
  res_bulk=requests.put(bulk_update_url,headers=headers,data=bulk_json)
  return res_bulk

def bulk_update_transcriptions(doc_pk,part_pk,transcriptions):
  bulk_update_url = get_part_transcriptions_base_url(doc_pk,part_pk)+'bulk_update/'
  bulk_json=json.dumps({'transcriptions': transcriptions}) # or should it say lines????
  res_bulk=requests.put(bulk_update_url,headers=headers,data=bulk_json)
  return res_bulk


# function-endpoints------------------------------------------------------------------------------

def import_xml(doc_pk,dirname,fname, name):
  """
  e.g. import_xml(3221,r'/content/','export_doc3221_trial_alto_202302231124.zip')
  """
  data={'name': name, 'document':doc_pk, 'task':'import-xml'}
  file = os.path.join(dirname, fname)
  import_url=get_specific_doc_url(doc_pk)+'imports/'
  with open(file,'rb') as fh:
    file_handler={'upload_file':fh}
    res=requests.post(import_url,headers=headersbrief,data=data,files=file_handler)
    print(res.status_code, res.content)
    return res

def export_xml(doc_pk,part_pk_list,tr_level_pk,region_type_pk_list,include_undefined = True, include_orphan = True, file_format = 'alto',include_images = False, print_status = True):
  export_url = get_specific_doc_url(doc_pk)+'export/' # e.g. https://escriptorium.openiti.org/api/documents/3221/export/
  if include_undefined:
    region_type_pk_list += 'Undefined'
  if include_orphan:
    region_type_pk_list += 'Orphan'
  data = {'parts': part_pk_list, 'transcription': tr_level_pk,'task': 'export','region_types':region_type_pk_list,'include_images':include_images,'file_format':file_format}
  #e.g. {"parts": [755434], "transcription": 5631, "task": "export", "region_types": [2,'Undefined','Orphan'], "include_images" : False, "file_format": "alto"}
  res = requests.post(export_url,data=data,headers=headersbrief)
  if print_status:
    print(res.status_code)
    print(res.content)
  return res

def segment(doc_pk,segmodel_pk,part_pk_list,steps,override = True,print_status = True):
  if not(steps in ['lines','both','regions','masks']):
    print('steps are not valid')
    juststop
  segment_url = get_segmentation_url(doc_pk)
  data = {'parts':part_pk_list,'model':segmodel_pk,'steps':steps,'override':override}
  r = requests.post(segment_url,data = json.dumps(data),headers = headers)
  if print_status:
    print(r.status_code)
  return r

def transcribe(doc_pk,trans_model_pk,part_pk_list,print_status = False):
  trans_url = get_transcribe_url(doc_pk)
  data = {'parts':part_pk_list,'model':trans_model_pk}
  #{parts: [1, 2], model: 1} {headers only with authorization}
  r = requests.post(trans_url,data = json.dumps(data),headers = headers)
  if print_status:
    print(r.status_code)
  return r

def move_part(doc_pk,part_pk,place):
    print('move part_pk '+str(part_pk)+'to place '+str(place))
    url=get_specific_part_url(doc_pk,part_pk)+'move/'
    data='{"index":'+str(place)+'}'
    res=requests.post(url,headers=headers,data=data)
    return res

def crop_part_img(doc_pk,part_pk,top,left,bottom,right,print_status = False):
  data = json.dumps({'x1':left, 'y1':top, 'x2' : right, 'y2':bottom})
  crop_url=get_specific_part_url(doc_pk,part_pk)+'crop/'
  r = requests.post(url = crop_url,headers = headers,data = data)
  if print_status:
    print(r.status_code)
  return r

def rotate_img(doc_pk,part_pk,angle,print_status = False):
  rotate_url=get_specific_part_url(doc_pk,part_pk)+'rotate/'
  data={'angle':angle}
  res=requests.post(url=rotate_url,headers=headers,data=json.dumps(data))
  if print_status:
    print(res.status_code)
  return res

def repolygonize(doc_pk,part_pk, print_progress = False, print_status= False):
    if print_progress:
      print('repolygonize : ',part_pk)
    url_repoly=get_specific_part_url(doc_pk,part_pk)+'reset_masks/'
    res=requests.post(url_repoly,headers=headers)
    if print_status:
      print(res.status_code)
    return res

def repolygonize_line(doc_pk,part_pk,line_pk):
    print('repolygonize line : ',line_pk)
    url_repoly=get_specific_part_url(doc_pk,part_pk)+'reset_masks/?only='+str(line_pk)
    r=requests.post(url_repoly,headers=headers)
    return r
    
def reorder(doc_pk,part_pk,print_progress=False, print_status = False):
    if print_progress:
      print('reorder ',part_pk)
    reorder_url=get_specific_part_url(doc_pk,part_pk)+'recalculate_ordering/'
    res = requests.post(reorder_url,headers=headers)
    if print_status:
      print(res.status_code)
    return res

def train(doc_pk,part_pk_list,model_name,tr_level_pk,on_top_model_pk,override = False):
  train_url = get_specific_doc_url(doc_url)+'train/'
  data = {'parts': part_pk_list,'model': on_top_model_pk, 'model_name': model_name,'transcription': tr_level_pk,'override': override  }
  r=requests.post(url= train_url,data=json.dumps(data),headers=headers)
  return r

def segtrain(doc_pk,part_pk_list,model_name,on_top_model_pk,override = False):
  segtrain_url = get_specific_doc_url(doc_url)+'segtrain/'
  data = {'parts': part_pk_list,'model': on_top_model_pk, 'model_name': model_name,'override': override  }
  r=requests.post(url= segtrain_url,data=json.dumps(data),headers=headers)
  return r

  # search-and-sort-----------------------------------------------------------------------
def search(pk, list_of_dictionaries):
    result_list=[element for element in list_of_dictionaries if element['pk'] == pk]
    if len(result_list)==1:
      return result_list  [0]
    elif len(result_list)==0:
      return None
    else:
      return result_list

def search_any(key, value, list_of_dictionaries):
    return [element for element in list_of_dictionaries if element[key] == value]

def filter_dict_list(key,key_val_list,list_of_dictionaries):
  if (isinstance(key_val_list,str)) or (not(isinstance(key_val_list,list))):
    return search_any(key, key_val_list, list_of_dictionaries)
  else:
    return [row for row in list_of_dictionaries if row.get(key) in key_val_list]

def find_substr_in_str(str,substr):
  return [m for m in re.finditer(substr, str)]

def replace_substr_in_str(str,substr,replacement):
  return re.sub(substr, replacement, str)

def get_idx(pk, list_of_dictionaries):
  result_list=[n for n,element in enumerate(list_of_dictionaries) if element['pk'] == pk]
  if len(result_list)==1:
    return result_list[0]
  elif len(result_list)==0:
    return None
  else:
    return result_list

def check_token_contains(key,chars,list_of_dictionaries):
  return [n for n,element in enumerate(list_of_dictionaries) if any((c in chars) for c in element[key])]

def find_string_in_page_transcription(doc_pk,part_pk,tr_level,query_string):
    transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
    transcription_txt = get_sthg_from_dict_list(transcriptions,'content')
    page_transcription = ' '.join(transcription_txt)
    return find_substr_in_str(page_transcription,query_string)

#-------------maths-----------------------------------------------------------------------------------------

def dist2points(x1,y1,x2,y2):
  dist=sqrt((x2 - x1)**2 + (y2 - y1)**2)
  return dist

def get_centroid(line):
  return [int(round((line[0][0]+line[-1][0])/2,0)),int(round((line[0][1]+line[-1][1])/2,0))]

def get_angle(line):
    return rad2deg(arctan2(line[-1][-1] - line[0][-1], line[-1][0] - line[0][0]))

def get_vector(angle,length):
  #from numpy import rad2deg,deg2rad,cos,sin
  #return rad2deg(arctan2(line[-1][-1] - line[0][-1], line[-1][0] - line[0][0]))
  #length=hypothenuse
  #ankathete=x
  #gegenkathete=y
  y=int(round(sin(deg2rad(angle))*length,0))
  x=int(round(cos(deg2rad(angle))*length,0))
  return x,y

def rotateNP(p, origin=(0, 0), degrees=0):
    angle = deg2rad(degrees)
    R = array([[cos(angle), -sin(angle)],
                  [sin(angle),  cos(angle)]])
    o = atleast_2d(origin)
    p = atleast_2d(p)
    return squeeze((R @ (p.T-o.T) + o.T).T)

def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])
    
    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        print('lines do not intersect')
        x = line1[0][0]
        y = 100000
    else:
        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
    return x, y

def float2int(x):
  return int(round(x,0))

def str2int(x):
  return int(round(float(x),0))

def list_of_str_points2int(list_of_points):
  upper_int = []
  for p in list_of_points:
    p_int = list()
    for c in p:
      p_int.append(str2int(c))
    upper_int.append(p_int)
  return upper_int

# check_validity--------------------------------------------------------------------------------
def check_point_in_image(p,imgHeight,imgWidth,safetydistance):
    # deal with x:
    p[0]=min(imgWidth-safetydistance,max(p[0],safetydistance))
    p[1]=min(imgHeight-safetydistance,max(p[1],safetydistance))
    return p  

def simplify_line_polygons_on_part(doc_pk,part_pk,simplification=10):
  lines_url=get_lines_url(doc_pk,part_pk)
  lines=loop_through_itempages_and_get_all(lines_url)
  for line in lines:
    mask=line['mask']
    #print(len(mask),mask)
    maskPoly=Polygon(mask)
    maskSimple=maskPoly.simplify(10)
    #print(maskSimple)
    x,y = maskSimple.exterior.coords.xy
    new_mask = [list(x) for x in zip(x,y)]
    #print(len(new_mask),new_mask)
    line_url = lines_url+str(line['pk'])+'/'
    line_json={'mask' : new_mask}
    res_line = requests.patch(line_url,headers=headers,data=json.dumps(line_json))


##############################################################################COMPLEX#######################################################################################

#@title complex
#%%writefile complex_api_functions.py

# find_and_replace_text_or_trim, transfer_txt2level, get_pages_without_transcription_level, get_pages_with_wordstring_in_transcription_level,
# delete_linefree_regions, keep_only_biggest_region, associate_lines_with_existing_regions, delete_unlinked_lines, delete_1p_lines,
# find_lines_without_mask, extend_lines, create_transcription_table, delete_empty_lines


def find_and_replace_chars(doc_pk,part_pk,tr_level,chars,replacement_char,do_replace):
  transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
  if do_replace:
    print('replacing '+chars+' with '+replacement_char)
    for m,line_tr in enumerate(transcriptions):
      oldstr=line_tr['content']
      if (any((c in chars) for c in oldstr)):
        content=line_tr['content']
        content=content.replace(chars,replacement_char)
        if not(oldstr==content):
          line_tr['content']=content
          tr_url = get_specific_transcription_url(doc_pk,part_pk,line_tr['pk'])
          res_patch=requests.patch(tr_url,headers=headers,data=json.dumps(line_tr['content']))
    return ''
  else:
    print('find pages with '+chars)
    chars=set(chars) 
    for m,line_tr in enumerate(transcriptions):
      linestr=line_tr['content']
      if any((c in chars) for c in linestr):
        print('have a look for character in ',part_pk,' line :',m,)
    return part_pk

def replace_string_or_trim(doc_pk,part_pk,tr_level,search_str,replacement_str,do_replace,do_trim=False):
  if do_replace:
    print('replacing '+search_str+' with '+replacement_str)
  if do_trim:
    print('trimming')
  transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
  for line_tr in transcriptions:
    oldstr = line_tr['content']
    if do_trim:
      line_tr['content'] = line_tr['content'].strip()
    if do_replace:
      line_tr['content'] = replace_substr_in_str(line_tr['content'],search_str,replacement_str)
    if not(oldstr == tr['content']):
      tr_url = get_specific_transcription_url(doc_pk,part_pk,line_tr['pk'])
      res_patch=requests.patch(tr_url,headers=headers,data=json.dumps(line_tr['content']))

def transfer_txt2level(doc_pk,part_pk,source_tr_level,target_tr_level,overwrite):
  target_tr_url=get_part_transcriptions_base_url(doc_pk,part_pk)
  source_transcriptions = get_page_transcription(doc_pk,part_pk,source_tr_level)
  target_transcriptions = get_page_transcription(doc_pk,part_pk,target_tr_level)
  target_tr_line_pks = get_sthg_from_dict_list(target_transcriptions,'line') # create list of existing target transcription line pks.
  for line_tr in source_transcriptions:
    line_pk = line_tr['line']
    data = {'line': line_pk, 'transcription': target_tr_level, 'content': line_tr['content']}
    if line_pk in target_tr_line_pks: # check if exists
      if overwrite:
        tg_line_pk = search_any('line',line_pk,target_transcriptions)[0]['pk']
        tr_url = get_specific_transcription_url(doc_pk,part_pk,tg_line_pk)
        res_patch = requests.patch(tr_url,headers=headers,data=json.dumps(data))
        print('Doing stuff at url: ', tr_url)
        if not(res_patch.status_code==200):
          print('error in patch',res_patch.status_code)
    else:
      res_post = requests.post(target_tr_url, data=json.dumps(data), headers=headers)
      print('Doing stuff at url: ', target_tr_url)
      if not(res_post.status_code==201):
          print('error in post',res_post.status_code)

def get_lines_without_transcription_level(doc_pk,part_pk,tr_level,also_empty_lines=False):
  print('check pages without transcription in transcription level for pk', part_pk)
  line_pks = set(get_line_pk_list(doc_pk,part_pk))
  transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
  if also_empty_lines:
    transcriptions = [tr for tr in transcriptions if len(tr['content'].trim())>0]
  tr_line_pks = set(get_sthg_from_dict_list[transcriptions,'line']) # create set of existing transcription line pks.
  missing=line_pks.difference(tr_line_pks)
  return missing
  
def find_or_delete_linefree_regions(doc_pk,part_pk,do_delete=False):
  inhabited_region_list=set(get_inhabited_region_pk_list(doc_pk,part_pk))
  region_list=set(get_region_pk_list(doc_pk,part_pk))
  uninhabited_region_list=region_list.difference(inhabited_region_list)
  for region in uninhabited_region_list:
    if do_delete:
      delete_region(doc_pk,part_pk,region)

def find_linefree_regions(doc_pk,part_pk):
  inhabited_region_list=set(get_inhabited_region_pk_list(doc_pk,part_pk))
  region_list=set(get_region_pk_list(doc_pk,part_pk))
  uninhabited_region_list=list(region_list - inhabited_region_list)
  return uninhabited_region_list
    

def keep_only_n_biggest_regions(doc_pk,part_pk,n):
  regions = get_all_regions_of_part(doc_pk,part_pk)
  for region in regions:
    region['area'] = Polygon(region['box']).area
  sorted_regions = sorted(regions,key=lambda i: i['area'], reverse = True)
  if len(sorted_regions)>n:
    for region in sorted_regions[n:]:
      print('delete ',region['pk'])
      delete_region(doc_pk,part_pk,region['pk'])
      
def associate_lines_with_existing_regions_and_reorder(doc_pk,part_pk, print_progress=False):
  if print_progress:
    print(part_pk)
  line_url=get_lines_url(doc_pk,part_pk)
  region_url=get_regions_url(doc_pk,part_pk)
  lines=loop_through_itempages_and_get_all(line_url)
  regions=loop_through_itempages_and_get_all(region_url)
  nu_regions=len(regions)
  region_pk_list = [item['pk'] for item in regions]
  updated_lines=list()
  for region in regions:
    region['poly'] = Polygon(region['box'])
  if print_progress:
    print('associating')
  for n,line in enumerate(lines):
    baseline=line['baseline']
    centroidx,centroidy=get_centroid(baseline)
    p = Point(centroidx, centroidy)
    for region in regions:
      if p.within(region['poly']) and not(line['region']==region['pk']):
        line['region']=region['pk']
        updated_lines.append(line)
        break
  if len(updated_lines)>0:
    if print_progress:
      print('putting')
      print(updated_lines)
    bulk_update_lines(doc_pk,part_pk,updated_lines)
    if print_progress:
      print('reordering')
    reorder(doc_pk,part_pk)

def find_or_delete_unlinked_lines(doc_pk,part_pk,do_delete=False):
  lines = get_all_lines_of_part(doc_pk,part_pk)
  lines2delete = list()
  for line_n,line in enumerate(lines): 
    if line['region']==None:
      print('found unassociated line in doc',doc_pk,', on part',part_pk,', line:',line_n)
      if do_delete:
        lines2delete.append(line['pk'])
  if len(lines2delete)>0:
    bulk_delete_lines(doc_pk,part_pk,lines2delete,False)
    reorder(doc_pk,part_pk)

def find_unlinked_lines(doc_pk,part_pk):
  lines = get_all_lines_of_part(doc_pk,part_pk)
  unlinked_lines_list = []
  for line_n,line in enumerate(lines):
    if line['region']==None:
      unlinked_lines_list.append(line_n)
  return unlinked_lines_list
    
def delete_1p_lines(doc_pk,part_pk):
  lines = get_all_lines_of_part(doc_pk,part_pk)
  lines2delete = list()
  for line_n,line in enumerate(lines): 
    if (len(line['baseline'])<2):
      print('need to delete line')
      lines2delete.append(line['pk'])
  if len(lines2delete)>0:
    bulk_delete_lines(doc_pk,part_pk,lines2delete,False)
    reorder(doc_pk,part_pk)
  
def find_lines_without_mask(doc_pk,part_pk):
  lines = get_all_lines_of_part(doc_pk,part_pk)
  maskless_lines = list()
  for line_n,line in enumerate(lines): 
    try:
      len_mask=len(line['mask'])
    except:
      len_mask=0
    if len_mask<4:
      #print('line in doc',doc_pk,'part',part_pk,'line',line_n,'with only',len_mask,'points')
      maskless_lines.append(line)
  return maskless_lines

def extend_lines(doc_pk,part_pk,extension=15,left_also=False,baseline2topline=False,y_decrease=10,repoly=True):
  lines = get_all_lines_of_part(doc_pk)
  pageheight,pagewidth=page_height_width(doc_pk,part_pk)
  for line in lines:
    baseline=line['baseline']
    line_id=line['pk']
    if baseline[0][0]<baseline[-1][0]:
      if left_also:
        baseline[0][0]=max(5,int(round((baseline[0][0])))-extension)
      baseline[-1][0]=min(int(round((baseline[-1][0])))+extension,pagewidth-5)
    else:
      if left_also:
        baseline[0][0]=min(int(round((baseline[0][0])))+extension,pagewidth-5)
      baseline[-1][0]=max(5,int(round((baseline[-1][0])))-extension)
    if baseline2topline:
      baseline=[[pt[0], max(5,pt[1]-y_decrease)] for pt in baseline]
    line['baseline'] = baseline
    bulk_update_lines(doc_pk,part_pk,lines,False)
  if repoly:
    repolygonize(doc_pk,part_pk)

def extend_lines_of_specific_linetype(doc_pk,part_pk,list_line_typologies_to_treat,extension=8,left_also=False,baseline2topline=False,y_decrease=10,repoly=True):
  lines = get_all_lines_of_part(doc_pk, part_pk)
  pageheight,pagewidth=page_height_width(doc_pk,part_pk)
  for line in lines:
    if line['typology'] in list_line_typologies_to_treat:
        baseline=line['baseline']
        line_id=line['pk']
        if baseline[0][0]<baseline[-1][0]:
          if left_also:
            baseline[0][0]=max(5,int(round((baseline[0][0])))-extension)
          baseline[-1][0]=min(int(round((baseline[-1][0])))+extension,pagewidth-5)
        else:
          if left_also:
            baseline[0][0]=min(int(round((baseline[0][0])))+extension,pagewidth-5)
          baseline[-1][0]=max(5,int(round((baseline[-1][0])))-extension)
        if baseline2topline:
          baseline=[[pt[0], max(5,pt[1]-y_decrease)] for pt in baseline]
        line['baseline'] = baseline
        bulk_update_lines(doc_pk,part_pk,lines)
  if repoly:
    create_normalized_polygons_around_typelist_lines(doc_pk,part_pk,correctionlinetypes=list_line_typologies_to_treat,ascender=30,descender=35,safetydistance=5)

def create_transcription_table(doc_pk,part_list,tr_level):
  pages=[]
  regions=[]
  line_pks=[]
  transcription_pks=[]
  linenumbers=[]
  txt=[]
  regions=[]
  for n,part_pk in enumerate(part_list):
  
    if n % 10 == 0:
      print(n)
    transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
    lines = get_all_lines_of_part(doc_pk,part_pk)
    regions = get_all_regions_of_part(doc_pk,part_pk)
    line_pk_list_this_transcription = [tr.get('line') for tr in transcriptions]
  
    line_pk_list_this_part = [line.get('pk') for line in lines]
    line2region_list_this_part = [line.get('region') for line in lines]
  
    region_pk_list_this_part = [region.get('pk') for region in regions]
  
    for line in lines:
      pages.append(n+1)
      line_pks.append(line['pk'])
      linenumbers.append(line['order']+1)
      try:
        regions.append(region_pk_list_this_part.index(line['region'])+1)
      except:
        regions.append(None)
      try:
        index=line_pk_list_this_transcription.index(line['pk'])
        transcription_pks.append(transcriptions[index]['pk'])
        txt.append(transcriptions[index]['content'])
      except:
        transcription_pks.append(None)
        txt.append('')
  print('done')

  columntitles = ['page', 'region', 'line','line_pk', 'transcription_pk','txt']
  data =[columntitles] + list(zip(pages, regions, linenumbers,line_pks,transcription_pks,txt))

  for i, d in enumerate(data):
    tableline = ' | '.join(str(x).ljust(4) for x in d)
    print(tableline)
    if i == 0:
      print('-' * len(tableline))

def delete_empty_lines(doc_pk,part_pk,tr_level,min_length=1):
  transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
  lines = get_all_lines_of_part(doc_pk,part_pk)
  line_pks = get_pks_of_dict_list(lines)
  lines2delete = list()
  for tr in transcriptions:
    if len(tr['content'])<min_length:
      lines2delete.append(tr['line'])
    line_pks.remove(tr['line'])
  for line_pk in line_pks:
    lines2delete.append(line_pk)
  if len(lines2delete)>0:
    bulk_delete_lines(doc_pk,part_pk,lines2delete,print_status = True)

def calculate_average_line_distance(baselineCoordsList,pageheight,pagewidth):
  average_line_height_list=[]
  midpointList = [[(line[0][0]+line[-1][0])/2,(line[0][1]+line[-1][1])/2] for line in baselineCoordsList]
  lineBegList = [line_intersection([[0,0],[0,pageheight]],[[line[0][0],line[0][1]],[line[-1][0],line[-1][1]]]) for line in baselineCoordsList]
  lineEndList = [line_intersection([[pagewidth,0],[pagewidth,pageheight]],[[line[0][0],line[0][1]],[line[-1][0],line[-1][1]]]) for line in baselineCoordsList]
  d_list=[]
  for n,midpoint in enumerate(midpointList):
    if n>0:
      p1=array(lineBegList[n-1])
      p2=array(lineEndList[n-1])
      p3=array(midpoint)
      d_list.append(cross(p2-p1,p3-p1)/linalg.norm(p2-p1))
    elif len(midpointList)>1:
      p1=array(lineBegList[n+1])
      p2=array(lineEndList[n+1])
      p3=array(midpoint)
      d_list.append(-(cross(p2-p1,p3-p1)/linalg.norm(p2-p1)))
    average_line_height=int(round(sum(d_list)/len(d_list),0))
    average_line_height_list.append(average_line_height)
  if average_line_height_list:
    return int(round(mean(average_line_height_list)))
  else:
    return -1

def restrict_first_and_last_line_polygon_according_to_average_line_height(doc_pk,part_pk,region_pk,average_line_distance=0):

  def repoly_extreme_line(line,direction):
    lines_url = get_lines_url(doc_pk,part_pk)
    # create dummy baseline above or below to limit extension of first or last line
    phantombaseline=[[pt[0], min(pageheight-5,max(5,pt[1]+(average_line_distance+5)*direction))] for pt in line[2]]
    phantom_data=json.dumps({'document_part':part_pk,'region':region_pk,'baseline':phantombaseline})
    phantom_line_pk=requests.post(lines_url,headers=headers,data=phantom_data).json()['pk']
    # repolygonize
    res=repolygonize_line(doc_pk,part_pk,line[0])
    print('repoly-response: ',res)
    # delete dummy line
    phantom_line_del=delete_line(doc_pk,part_pk,phantom_line_pk,headers=headers)
  print(average_line_distance)
  pageheight,pagewidth=page_height_width(doc_pk,part_pk)
  all_lines_this_region=get_all_lines_of_region(doc_pk,part_pk,region_pk)
# main lines only
  main_lines_this_region =[line for line in all_lines_this_region if line['typology'==None]]
  baselineCoordsList=[line[2] for line in main_lines_this_region]
# calculate average line distance
  if average_line_distance==0:
    average_line_distance=calculate_average_line_distance(baselineCoordsList,pageheight,pagewidth)
  if (average_line_distance>5) and (len(main_lines_this_region)>0):
# treat first line
    index_first = min(lines[1] for lines in main_lines_this_region)
    line_first=[line for line in main_lines_this_region if line[1]==index_first]
    line_first=line_first[0]
    repoly_extreme_line(line_first,-1)    
# treat last line
    index_last = max(lines[1] for lines in main_lines_this_region)
    if not(index_last==index_first):
      line_last=[line for line in main_lines_this_region if line[1]==index_last]
      line_last=line_last[0]
      repoly_extreme_line(line_last,1)
      print('repolygonized extremes of part: ',part_pk)
  else:
    print('not able to calculate average line distance for part: ',part_pk)
  return average_line_distance

def create_normalized_polygons_around_CORRECTION_lines(doc_pk,part_pk,ascender=12,descender=24,correctionlinetype=3,safetydistance=5):

  pageheight,pagewidth=page_height_width(doc_pk,part_pk)
  ## first loop: calculate average line height and distance
  region_list=get_main_region_pk_list(doc_pk,part_pk)
  for m,region_pk in enumerate(region_list):
    all_lines_this_region=get_all_lines_of_region(doc_pk,part_pk,region_pk)
    correction_lines_this_region = [line for line in all_lines_this_region if line['typology']==correctionlinetype]
    for line in correction_lines_this_region:
      baseline = line['baseline']
      old_pt=baseline[0]
      for o,pt in enumerate(baseline[1:]):          
        #print('region '+str(m)+', line '+str(n)+', point '+str(o)+str(old_pt)+':'+str(pt))
        angle=get_angle([old_pt,pt])
        if o==0:
          inside_above=False
          inside_below=False
          new_pt_above=rotateNP((old_pt[0],old_pt[1]-ascender),origin=tuple(old_pt),degrees=angle)
          new_pt_below=rotateNP((old_pt[0],old_pt[1]+descender),origin=tuple(old_pt),degrees=angle)
          #print(new_pt_above,pageheight,pagewidth,safetydistance)
          new_pt_above=check_point_in_image(new_pt_above,pageheight,pagewidth,safetydistance)
          new_pt_below=check_point_in_image(new_pt_below,pageheight,pagewidth,safetydistance)
          #print(new_pt_above)
          polygon_above=[[int(coordinate) for coordinate in new_pt_above]]
          polygon_below=[[int(coordinate) for coordinate in new_pt_below]]
        new_pt_above=[int(coordinate) for coordinate in rotateNP((pt[0],pt[1]-ascender),origin=tuple(pt),degrees=angle)]
        new_pt_below=[int(coordinate) for coordinate in rotateNP((pt[0],pt[1]+descender),origin=tuple(pt),degrees=angle)]
        new_pt_above=check_point_in_image(new_pt_above,pageheight,pagewidth,safetydistance)
        new_pt_below=check_point_in_image(new_pt_below,pageheight,pagewidth,safetydistance)
        if o>0:
          if inside_above and not(o==len(line[1:])): # if point is inside and is not the last point, # delete previous point, dont insert next point either # and insert instead the intersection of (p-2:p-1) and (p:p+1)
            replace_pt=list(line_intersection([polygon_above[-3],polygon_above[-2]],[polygon_above[-1],new_pt_above]))
            del polygon_above[-2:-1]
            polygon_above.append(replace_pt)
          if inside_below:
            replace_pt=list(line_intersection([polygon_below[2],polygon_below[1]],[polygon_below[0],new_pt_below]))
            del polygon_below[0:1]
            polygon_below.insert(0,replace_pt)
          pol=Polygon(polygon_above+polygon_below)
          inside_above=pol.contains(Point(new_pt_above))
          inside_below=pol.contains(Point(new_pt_below))
        polygon_above.append(new_pt_above) # if point is outside add it to boundary
        polygon_below.insert(0,new_pt_below) # if point is outside add it to boundary
        old_pt=pt
      if inside_above:
        del polygon_above[-1] # if point is inside and is last point delete it
      if inside_below:
        del polygon_below[0] # if point is inside and is last point delete it
      polygon_boundary=polygon_above+polygon_below
      line['mask']=polygon_boundary
    bulk_update_lines(doc_pk,part_pk,correction_lines_this_region)  
    
def simplify_hebrew(doc_nu,part_list,source_tr_level,target_tr_level):
    vocalization=[1425,1427,1430,1436,1438,1443,1446,1453,1456,1457,1458,1459,1460,1461,1462,1463,1464,1465,1466,1467,1468,1469,1471,1473,1474,1476,1477,1478,1479]
    singlequot=[1523,8216,8217,8219,8242]
    doublequot=[1524,8220,8221,8222,8223,8243]
    spacechars=[9,160,8201,8195,8192]
    deletechars=[1565,8299,8205,8300,8302]
    toreplacechars=[(64296,1514),(64298,1513),(64299,1513),(64300,1513),(64302,1488),(64303,1488),(64305,1489),(64306,1490),(64307,1491),(64309,1493),(64315,1499),(64324,1508),(64327,1511),(64330,1514),(64331,1493),(64332,1489),(64333,1499),(64334,1508),(8277,42),(8283,46),(11799,61)]
    for n,part in enumerate(part_list[41:]):
        target_tr_url=root_url+'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/transcriptions/'
        #https://www.escriptorium.fr/api/documents/39/parts/14480/transcriptions/?page=2&transcription=46
        page_nu=0
        while True:
            page_nu+=1
            source_tr_url=root_url+'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/transcriptions/'+'?page='+str(page_nu)+'&transcription='+str(source_tr_level)
            target_tr_url=root_url+'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/transcriptions/'+'?page='+str(page_nu)+'&transcription='+str(target_tr_level)
            res = requests.get(source_tr_url, headers=headers).json()
            print(source_tr_url)
            res_target=requests.get(target_tr_url, headers=headers).json()
            if res_target!={'detail': 'Invalid page.'}:
                target_line_pk_list = [line['line'] for line in res_target['results']]
                target_tr_pk_list = [line['pk'] for line in res_target['results']]
                print(target_line_pk_list)
            else:
                target_line_pk_list=[]
                target_tr_pk_list=[]
            #print(res_target)
            for m,line in enumerate(res['results']):
                #'line': 674381, 'transcription': 46, 'content': 'מדביק מרחם שערים הליכות מצויינים', 
                line_pk=line['line']
                print(line_pk)
                print(line['pk'])
                content=line['content']
                for u in vocalization:
                    content=content.replace(chr(u),'')
                for u in spacechars:
                    content=content.replace(chr(u),' ')
                for u in deletechars:
                    content=content.replace(chr(u),'')
                for u in singlequot:
                    content=content.replace(chr(u),"'")
                for u in doublequot:
                    content=content.replace(chr(u),'"')
                for (x,y) in toreplacechars:
                    content=content.replace(chr(x),chr(y))
                data = {'line': line_pk, 'transcription': target_tr_level, 'content': content}
                if line_pk in target_line_pk_list:
                    t_url=(root_url+'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/transcriptions/'+str(line['pk'])+'/')
                    res_t=requests.get(t_url,headers=headers).json()
                    print('put',res_t['content'])
                    res_t['content']=content
                    print(t_url)
                    data=json.dumps(res_t, ensure_ascii=False).encode('utf8')
                    res_put = requests.put(t_url, data=data, headers=headers)
                    #print('put',res_put.content)
                else:
                    res_post = requests.post(target_tr_url, data=json.dumps(data), headers=headers)
                    #print(n,part,m,res_post.content)
            if not(res['next']):
                break
    print('done simplifying hebrew')

def delete_text_in_main_regions_except_line_type(doc_nu,part_list,tr_level,allowed_line_types):
    
    for n,part_pk in enumerate(part_list):
        print(n,part_pk)
        #get all main regions
        regions = get_all_regions_of_part(doc_pk,part_pk)
        main_region_list=[r.get('pk') for r in regions['results'] if r['typology']==2]
        
        #get all lines of this part that are in the main columns and of the default type and delete their content      
        page_nu=0
        del_lines_pk_list=[]
        lines = get_all_lines_of_part(doc_pk,part_pk)
        for line in lines:
          if (not(line['typology'] in allowed_line_types)) and (line['region'] in main_region_list):
            del_lines_pk_list.append(line['pk'])
        transcriptions = get_page_transcription(doc_pk,part_pk,tr_level)
        delete_tr_list = list()
        for tr_line in transcriptions:
          if tr_line['line'] in del_lines_pk_list:
            delete_tr_list.append(tr_line['pk'])
        bulk_delete_transcriptions(doc_pk,part_pk,delete_tr_list)

def loop_document_restrict_extreme_lines_all_regions(doc_pk,fix_line_height,start_item=0):

  part_pk_list,tr_level_list,region_type_list,line_type_list=get_basic_info(doc_pk)
  for part_pk in part_pk_list[start_item:]:
    print('----------------------------------------------------')
    print('resegmenting part :',part_pk)
    region_list=get_region_pk_list(doc_pk,part_pk)
    main_region_list=get_main_region_pk_list(doc_pk,part_pk)
    average_line_height_in_main_regions=[]
    for region_pk in main_region_list:
      average_line_height_in_main_regions.append(restrict_first_and_last_line_polygon_according_to_average_line_height(doc_pk,part_pk,region_pk,fix_line_height))
    if len(main_region_list)>0:
      global_average_line_height=mean(average_line_height_in_main_regions)
    else:
      global_average_line_height=fix_line_height
    non_main_regions=set(region_list)-set(main_region_list)
    for region_pk in non_main_regions:
      line_height=restrict_first_and_last_line_polygon_according_to_average_line_height(doc_pk,part_pk,region_pk,global_average_line_height)
  
  print('done')

def create_normalized_polygons_around_lines(doc_nu,splitfactor=0.6,safetydistance=5,basic_line_height=120):
    
    part_list,tr_level_list,region_type_list,line_type_list=get_basic_info(doc_nu)
          
    for n,part in enumerate(part_list):
        parts_url = urljoin(root_url,'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/')
        res = requests.get(parts_url,headers=headers).json()
        pagewidth=res['image']['size'][0]
        pageheight=res['image']['size'][1]
        print(parts_url)
        ## first loop: calculate average line height and distance
        regionList = [region for region in res['regions']]
        average_line_height_list=[]
        average_line_height_not_null=[]
        for m,region in enumerate(regionList):
            baselineCoordsList = [line['baseline'] for line in res['lines'] if line['region']==regionList[m]['pk']]
            midpointList = [[(line[0][0]+line[-1][0])/2,(line[0][1]+line[-1][1])/2] for line in baselineCoordsList]
            lineBegList = [line_intersection([[0,0],[0,pageheight]],[[line[0][0],line[0][1]],[line[-1][0],line[-1][1]]]) for line in baselineCoordsList]
            lineEndList = [line_intersection([[pagewidth,0],[pagewidth,pageheight]],[[line[0][0],line[0][1]],[line[-1][0],line[-1][1]]]) for line in baselineCoordsList]
            d_list=[]
            for n,midpoint in enumerate(midpointList):
                if n>0:
                    p1=array(lineBegList[n-1])
                    p2=array(lineEndList[n-1])
                    p3=array(midpoint)
                    d_list.append(cross(p2-p1,p3-p1)/linalg.norm(p2-p1))
                elif len(midpointList)>1:
                    p1=array(lineBegList[n+1])
                    p2=array(lineEndList[n+1])
                    p3=array(midpoint)
                    d_list.append(-(cross(p2-p1,p3-p1)/linalg.norm(p2-p1)))
            if not(d_list):
                print('one line region')
                average_line_height_list.append(0)
            else:
                average_line_height=int(round(sum(d_list)/len(d_list),0))
                average_line_height_list.append(average_line_height)
                average_line_height_not_null.append(average_line_height)
        print(average_line_height_list)
        print(average_line_height_not_null)
        if not(average_line_height_not_null):
            global_average_line_height=basic_line_height
            print('bad average line height')
        else:
            global_average_line_height=int(round(sum(average_line_height_not_null)/len(average_line_height_not_null),0))
            print(global_average_line_height)
        
        for m,region in enumerate(regionList):
            if average_line_height_list[m]==0:
                this_line_height=global_average_line_height
            else:
                this_line_height=average_line_height_list[m]
            baselineCoordsList = [line['baseline'] for line in res['lines'] if line['region']==regionList[m]['pk']]
            baselinePKList = [line['pk'] for line in res['lines'] if line['region']==regionList[m]['pk']]
            for n,line in enumerate(baselineCoordsList):
                old_pt=line[0]
                for o,pt in enumerate(line[1:]):                    
                    #print('region '+str(m)+', line '+str(n)+', point '+str(o)+str(old_pt)+':'+str(pt))
                    angle=get_angle([old_pt,pt])
                    if o==0:
                        inside_above=False
                        inside_below=False
                        new_pt_above=rotateNP((old_pt[0],old_pt[1]-this_line_height*splitfactor),origin=tuple(old_pt),degrees=angle)
                        new_pt_below=rotateNP((old_pt[0],old_pt[1]+this_line_height*(1-splitfactor)),origin=tuple(old_pt),degrees=angle)
                        #print(new_pt_above,pageheight,pagewidth,safetydistance)
                        new_pt_above=check_point_in_image(new_pt_above,pageheight,pagewidth,safetydistance)
                        new_pt_below=check_point_in_image(new_pt_below,pageheight,pagewidth,safetydistance)
                        #print(new_pt_above)
                        polygon_above=[[int(coordinate) for coordinate in new_pt_above]]
                        polygon_below=[[int(coordinate) for coordinate in new_pt_below]]
                    new_pt_above=[int(coordinate) for coordinate in rotateNP((pt[0],pt[1]-this_line_height*splitfactor),origin=tuple(pt),degrees=angle)]
                    new_pt_below=[int(coordinate) for coordinate in rotateNP((pt[0],pt[1]+this_line_height*(1-splitfactor)),origin=tuple(pt),degrees=angle)]
                    new_pt_above=check_point_in_image(new_pt_above,pageheight,pagewidth,safetydistance)
                    new_pt_below=check_point_in_image(new_pt_below,pageheight,pagewidth,safetydistance)
                    if o>0:
                        if inside_above and not(o==len(line[1:])): # if point is inside and is not the last point, # delete previous point, dont insert next point either # and insert instead the intersection of (p-2:p-1) and (p:p+1)
                            replace_pt=list(line_intersection([polygon_above[-3],polygon_above[-2]],[polygon_above[-1],new_pt_above]))
                            del polygon_above[-2:-1]
                            polygon_above.append(replace_pt)
                        if inside_below:
                            replace_pt=list(line_intersection([polygon_below[2],polygon_below[1]],[polygon_below[0],new_pt_below]))
                            del polygon_below[0:1]
                            polygon_below.insert(0,replace_pt)
                        pol=Polygon(polygon_above+polygon_below)
                        inside_above=pol.contains(Point(new_pt_above))
                        inside_below=pol.contains(Point(new_pt_below))
                    polygon_above.append(new_pt_above) # if point is outside add it to boundary
                    polygon_below.insert(0,new_pt_below) # if point is outside add it to boundary
                    old_pt=pt
                if inside_above:
                    del polygon_above[-1] # if point is inside and is last point delete it
                if inside_below:
                    del polygon_below[0] # if point is inside and is last point delete it
                polygon_boundary=polygon_above+polygon_below
                line_url = urljoin(root_url,'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/lines/'+str(baselinePKList[n])+'/')
                resline = requests.get(line_url,headers=headers).json()
                resline['mask']=polygon_boundary
                data=json.dumps(resline)
                rput = requests.put(line_url,headers=headers,data=data)
                print(m,rput)
    print('done')

def create_normalized_polygons_around_typelist_lines(doc_pk,part_pk,correctionlinetypes,ascender=12,descender=24,safetydistance=5):

  pageheight,pagewidth=page_height_width(doc_pk,part_pk)
  lines = get_all_lines_of_part(doc_pk,part_pk)
  ## first loop: calculate average line height and distance
  region_list=get_main_region_pk_list(doc_pk,part_pk)
  correction_lines_this_region = [line for line in lines if line['typology'] in correctionlinetypes]
  for line in correction_lines_this_region:
    baseline = line['baseline']
    old_pt=baseline[0]
    for o,pt in enumerate(baseline[1:]):          
      #print('region '+str(m)+', line '+str(n)+', point '+str(o)+str(old_pt)+':'+str(pt))
      angle=get_angle([old_pt,pt])
      if o==0:
        inside_above=False
        inside_below=False
        new_pt_above=rotateNP((old_pt[0],old_pt[1]-ascender),origin=tuple(old_pt),degrees=angle)
        new_pt_below=rotateNP((old_pt[0],old_pt[1]+descender),origin=tuple(old_pt),degrees=angle)
        #print(new_pt_above,pageheight,pagewidth,safetydistance)
        new_pt_above=check_point_in_image(new_pt_above,pageheight,pagewidth,safetydistance)
        new_pt_below=check_point_in_image(new_pt_below,pageheight,pagewidth,safetydistance)
        #print(new_pt_above)
        polygon_above=[[int(coordinate) for coordinate in new_pt_above]]
        polygon_below=[[int(coordinate) for coordinate in new_pt_below]]
      new_pt_above=[int(coordinate) for coordinate in rotateNP((pt[0],pt[1]-ascender),origin=tuple(pt),degrees=angle)]
      new_pt_below=[int(coordinate) for coordinate in rotateNP((pt[0],pt[1]+descender),origin=tuple(pt),degrees=angle)]
      new_pt_above=check_point_in_image(new_pt_above,pageheight,pagewidth,safetydistance)
      new_pt_below=check_point_in_image(new_pt_below,pageheight,pagewidth,safetydistance)
      if o>0:
        if inside_above and not(o==len(line[1:])): # if point is inside and is not the last point, # delete previous point, dont insert next point either # and insert instead the intersection of (p-2:p-1) and (p:p+1)
          replace_pt=list(line_intersection([polygon_above[-3],polygon_above[-2]],[polygon_above[-1],new_pt_above]))
          del polygon_above[-2:-1]
          polygon_above.append(replace_pt)
        if inside_below:
          replace_pt=list(line_intersection([polygon_below[2],polygon_below[1]],[polygon_below[0],new_pt_below]))
          del polygon_below[0:1]
          polygon_below.insert(0,replace_pt)
        pol=Polygon(polygon_above+polygon_below)
        inside_above=pol.contains(Point(new_pt_above))
        inside_below=pol.contains(Point(new_pt_below))
      polygon_above.append(new_pt_above) # if point is outside add it to boundary
      polygon_below.insert(0,new_pt_below) # if point is outside add it to boundary
      old_pt=pt
    if inside_above:
      del polygon_above[-1] # if point is inside and is last point delete it
    if inside_below:
      del polygon_below[0] # if point is inside and is last point delete it
    polygon_boundary=polygon_above+polygon_below
    line['mask']=polygon_boundary
  bulk_update_lines(doc_pk,part_pk,correction_lines_this_region) 
    
def merge2levels_in_third(doc_pk,part_pk,level1,level2,level3):
  lines_without_master_transcription,proportion,empty_lines=get_lines_without_transcription_level(doc_pk,part_pk,level1)
  if proportion>0.3:
    lines_without_level2_transcription,proportion_level2,empty_lines=get_lines_without_transcription_level(doc_pk,part_pk,level2)
    if proportion_verso<0.3:
      print('from level2 to master on part ',part_pk)
      transfer_txt2level(doc_pk,part_pk,level2,level3)
    else:
      print('from level1 to master on part ',part_pk)
      transfer_txt2level(doc_pk,part_pk,level1,level3)
  else:
    print('master exists for part ',part_pk)

def change_all_regions2main(dok_pk):
  part_pk_list,tr_level_list,region_type_list,line_type_list=get_basic_info(doc_pk)
  for n,part_pk in enumerate(part_pk_list):
    region_list=get_region_pk_list(doc_pk,part_pk)
    for region_pk in region_list:
      regions_url = root_url+'api/documents/'+str(doc_pk)+'/parts/'+str(part_pk)+'/blocks/'+str(region_pk)+'/'
      res=requests.get(regions_url,headers=headers).json()
      print(n,res['typology'])
      if not(res['typology']==2):
        res['typology']=2
        data=json.dumps(res)
        res2=requests.put(regions_url,headers=headers,data=data)
        print(regions_url)
        print(res2)

def plot_polygon(Polygon):
  import matplotlib.pyplot as plt

  plt.plot(*Polygon.exterior.xy)
  #plt.plot(*maskSimple.exterior.xy)

def move_line_up_down(baseline,distance,down,pageheight,pagewidth):
  #down=1
  #up=-1
  safety=5
  angle=get_angle(baseline)
  # 0=horizontal
  if abs(angle)<45:
    if baseline[0][0]<baseline[-1][0]:
      vectorx,vectory=get_vector(angle+90*down,distance) #(LTR)
    else:
      vectorx,vectory=get_vector(angle+90*down,distance) #(RTL) (upside down)
  else:
    if baseline[0][1]<baseline[-1][1]:
      vectorx,vectory=get_vector(angle+90*down,distance) #(vertical up)
    else:
      vectorx,vectory=get_vector(angle+90*down,distance) #(vertical down)
  new_baseline=[[max(safety,min(pagewidth-safety,p[0]+vectorx)),max(safety,min(pageheight-safety,p[1]+vectory))] for p in baseline]
  return(new_baseline)

def extend_single_line(baseline,distance,do_left,do_right,pageheight,pagewidth):
  angle=get_angle(baseline)
  # 0=horizontal
  vectorx,vectory=get_vector(angle,distance)
  p1=baseline[0]
  pz=baseline[-1]
  p0=[]
  pend=[]
  if abs(angle)<45:
    if baseline[0][0]<baseline[-1][0]:
      if do_left:
        p0=[[max(1,min(pagewidth,p1[0]-vectorx)),max(1,min(pageheight,p1[1]-vectory))]]
      if do_right:
        pend=[[max(1,min(pagewidth,pz[0]+vectorx)),max(1,min(pageheight,pz[1]+vectory))]]
    else:
      if do_left:
        p0=[[max(1,min(pagewidth,p1[0]+vectorx)),max(1,min(pageheight,p1[1]+vectory))]]
      if do_right:
        pend=[[max(1,min(pagewidth,pz[0]-vectorx)),max(1,min(pageheight,pz[1]-vectory))]]
  else:
    if baseline[0][1]<baseline[-1][1]:
      if do_left:
        p0=[[max(1,min(pagewidth,p1[0]-vectorx)),max(1,min(pageheight,p1[1]-vectory))]]
      if do_right:
        pend=[[max(1,min(pagewidth,pz[0]+vectorx)),max(1,min(pageheight,pz[1]+vectory))]]
    else:
      if do_left:
        p0=[[max(1,min(pagewidth,p1[0]-vectorx)),max(1,min(pageheight,p1[1]-vectory))]]
      if do_right:
        pend=[[max(1,min(pagewidth,pz[0]+vectorx)),max(1,min(pageheight,pz[1]+vectory))]]
  if not(p0==[]):
    baseline=baseline[1:]
  if not(pend==[]):
    baseline=baseline[:-1]
  new_baseline=p0+baseline+pend
  return(new_baseline)


def move_all_lines_of_part_up_down(doc_pk,part_pk,distance=10,down=1,repoly=True, output=False):
  line_list=get_all_full_lines_of_part(doc_pk,part_pk) 
  #[[line['pk'],line['order'],line['baseline'],line['typology'],line['region']] for line in data['results']]
  pageheight,pagewidth=page_height_width(doc_pk,part_pk)
  print(part_pk)
  for line in line_list:
    baseline=line['baseline']
    line_id=line['pk']
    new_baseline=move_line_up_down(baseline,distance,down,pageheight,pagewidth)
    if output:
      #print('angle:',int(round(angle,0)))
      print('old: ',baseline)
      print('new: ',new_baseline)
    line_url = root_url+'api/documents/'+str(doc_pk)+'/parts/'+str(part_pk)+ '/lines/' + str(line_id) + '/'
    line_json = requests.get(line_url,headers=headers).json()
    line_json['baseline']=new_baseline
    res_line = requests.put(line_url,headers=headers,data=json.dumps(line_json))
  if repoly:
    url_repoly=root_url+'api/documents/'+str(doc_pk)+'/parts/'+str(part_pk)+'/reset_masks/'
    repoly_res=requests.post(url_repoly,headers=headers)

def calculate_regions_for_unlinked_lines(doc_nu,part,margin_type,paratext_type):
# calculate regions for unlinked lines by taking the minima and maxima of their boundaries
    from shapely.ops import cascaded_union
		
    
    parts_url = urljoin(root_url,'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/')
    print(parts_url)
    res = requests.get(parts_url,headers=headers).json()
    regpoly_list=[]
    line_links_list=[]
 
    for line_n,lines in enumerate(res['lines']): 
        if lines['region']==None: 
            line_array=array(lines['mask'])    
            try:
                x1 = min(line_array[:,0])
                y1 = min(line_array[:,1])
                x2 = max(line_array[:,0])
                y2 = max(line_array[:,1])
                poly = Polygon([[x1,y1],[x2,y1],[x2,y2],[x1,y2]])
                if len(regpoly_list)==0:
                    regpoly_list.append(poly)
                    line_links_list=[[line_n]]
                else:
                    no_join_found = True
                    for n,poly1 in enumerate(regpoly_list):
                        if poly.intersects(poly1): #poly overlaps with poly1 :
                    # merge: https://deparkes.co.uk/2015/02/28/how-to-merge-polygons-in-python/
                            polygons = [poly1, poly]
                            union_poly = cascaded_union(polygons)
                    # replace poly1 by union_poly
                            regpoly_list[n] = union_poly
                            poly = union_poly
                            line_links_list[n].append(line_n)
                            no_join_found = False
                    if no_join_found:
                        regpoly_list.append(poly)
                        line_links_list.append([line_n])
            except:
                print('error at:',str(part))
    blocks_url=root_url+'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/'
    data=requests.get(blocks_url,headers=headers).json()
    existing_regions=data['regions']
    post_url = root_url+'api/documents/'+str(doc_nu)+'/parts/'+str(part)+ '/blocks/'
    max_region_n=-1
    if len(existing_regions)==0:
        max_region_size=0
        for region_n,region in enumerate(regpoly_list):
            this_region_area=region.area
            if this_region_area>max_region_size:
                max_region_size=this_region_area
                max_region_n=region_n        
        maincol=regpoly_list[max_region_n]
        maincol_point_list = [[int(float(j)) for j in i] for i in list(maincol.exterior.coords)]
        block_json={'document_part': part,'box': maincol_point_list,'typology': 2}
        r = requests.post(post_url,headers=headers, data=json.dumps(block_json))
        y_main_min = min(array(maincol_point_list)[:,1])
        y_main_max = max(array(maincol_point_list)[:,1])
    else:
        y_main_min=10000
        y_main_max=0
        for region in existing_regions:
            if len(region['box'])<3:
                print('delete '+str(region['pk']))
                delete_url=root_url+'api/documents/'+str(doc_nu)+'/parts/'+str(part)+ '/blocks/'+str(region['pk']) + '/'
                r = requests.delete(delete_url,headers=headers)
                print(r.status_code)
            else:
                maincol=Polygon(region['box'])
                y1 = min(array(region['box'])[:,1])
                if y1<y_main_min:
                    y_main_min=y1
                y2 = max(array(region['box'])[:,1])
                if y2>y_main_max:
                    y_main_max=y2
    if max_region_n>-1:
        del regpoly_list[max_region_n] # KICK MAINCOL out of REGPOLYLIST
    for region_n,poly in enumerate(regpoly_list):
        poly_point_list = [[int(float(j)) for j in i] for i in list(poly.exterior.coords)]
        y_poly = mean(array(poly_point_list)[:,1])
        if (y_poly<y_main_min) or (y_poly>y_main_max):
            region_type=paratext_type
        else:
            region_type=margin_type
        block_json={'document_part': part,'box': poly_point_list,'typology': region_type}
        r = requests.post(post_url,headers=headers, data=json.dumps(block_json))
    reorder_url=root_url+'api/documents/'+str(doc_nu)+'/parts/'+str(part)+'/recalculate_ordering/'
    reorder_res = requests.post(reorder_url,headers=headers)
