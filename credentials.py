import copy

# Server connection informations
serverconnections = [
    {'servername':'msIA',
    'headers' : {'Authorization' : 'Token  aa12ccea8d0bf9f66a343592b799bb337f98a2d5'},
    'root_url' : 'https://msia.escriptorium.fr'},
    {'servername':'openITI',
     'headers' : {'Authorization' : 'YOUR_TOKEN'},
     'root_url' : 'https://escriptorium.openiti.org'}
    ]

# Set headers for all servers
for serverconnection in serverconnections:
    serverconnection['headersbrief'] = copy.deepcopy(serverconnection['headers'])
    serverconnection['headers']['Content-type'] = 'application/json'
    serverconnection['headers']['Accept']= 'application/json'

def search_any(key, value, list_of_dictionaries):
    return [element for element in list_of_dictionaries if element[key] == value]

def get_serverinfo(servername,serverconnections):
  serverconnection=search_any('servername', servername, serverconnections)[0]
  print('switching to ',servername)
  headers = serverconnection['headers']
  headersbrief = serverconnection['headersbrief']
  root_url = serverconnection['root_url']
  return root_url,headers,headersbrief




# 'headers' : {'Authorization' : 'Token  aa12ccea8d0bf9f66a343592b799bb337f98a2d5'}