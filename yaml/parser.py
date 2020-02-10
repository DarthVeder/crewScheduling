import yaml

with open(r'aircrafts.yml') as file:
    documents = yaml.full_load(file)

    for item, doc in documents.items():
        print(item, ":", doc)

    print(documents)


    print(str(documents['B744']['range'])+' nm')
