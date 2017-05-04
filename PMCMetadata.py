#########################################
###### PMC METADATA TO RDF TRIPLES ######
#########################################


# import needed libraries
import os
import sys
import pubmed_parser as pp  # pip install git+https://github.com/titipata/pubmed_parser.git
from rdflib import Namespace
from rdflib.namespace import RDF, FOAF, DCTERMS, RDFS
from rdflib import Graph
from rdflib import URIRef, Literal, BNode
import base64
import hashlib
import multiprocessing



def BibParser(item):
    '''
    Function is designed to take a nxml file with file path, parse it, and then return a list containing the
    specific values of interest.
    :param item: string containing the path to a nxml file
    :return: list of specific information parsed from the nxml file
    '''

    # parse dictionary
    dict1 = pp.parse_pubmed_xml(item)

    # get publication info
    pmid = dict1['pmid']
    pmcid = dict1['pmc']
    title = dict1['full_title'].encode('utf8')
    doi = dict1['doi']
    date = dict1['publication_year']
    authors = [x[:-1] for x in dict1['author_list']]
    journal = dict1['journal']

    return pmcid, pmid, title, doi, date, journal, authors



def TripleMaker(file_dir):
    '''
    function takes a list of directories and for each directory parses the .nxml file and creates a graph
    that is populated with specific triples using the parsed information. For each directory, a xml file is
    created which contains the triples and has been serialized to turtle format.
    :param file_dir: a list of directories
    :return: nothing is returned
    '''
    g = Graph() # create graph to store triples

    #add namespaces
    ccp_ext = Namespace("http://ccp.ucdenver.edu/obo/ext/")
    bibo = Namespace("http://purl.org/ontology/bibo/")
    obo = Namespace("http://purl.obolibrary.org/obo/")
    edam = Namespace("http://edamontology.org/")
    swo = Namespace("http://www.ebi.ac.uk/swo/")

    # iterate over folders within the input directory
    for subdir, dirs, files in os.walk(file_dir):
        for sub_file in files:
            item = os.path.join(subdir, sub_file)
            if item.endswith('.nxml.gz'):
                c_inf = BibParser(item)

                #create triples - article class
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0])), RDFS.subClassOf, URIRef(str(obo) + 'IAO_0000311')))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0])), URIRef(str(bibo) + 'pmid'), Literal(str(c_inf[1]))))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0])), URIRef(str(ccp_ext) + 'BIBO_EXT_0000001'), Literal('PMC' + str(c_inf[0]))))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0])), DCTERMS.title, Literal(str(c_inf[2]))))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0])), URIRef(str(bibo) + 'doi'), Literal(str(c_inf[3]))))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0])), DCTERMS.published, Literal(str(c_inf[4]))))
                g.add((URIRef(str(ccp_ext) + 'J_' + base64.b64encode(hashlib.sha1(str(c_inf[5])).digest())), DCTERMS.title, Literal(str(c_inf[5]))))
                g.add((URIRef(str(ccp_ext) + 'J_' + base64.b64encode(hashlib.sha1(str(c_inf[5])).digest())),
                       RDF.type, URIRef(str(bibo) + 'Journal')))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0])), URIRef(str(obo) + 'BFO_0000050'), URIRef(str(ccp_ext) + 'J_' + base64.b64encode(hashlib.sha1(str(c_inf[5])).digest()))))

                for author in c_inf[6]:
                    a_hash = base64.b64encode(hashlib.sha1(str(author[1]) + str(author[0])).digest())
                    g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0])), DCTERMS.creator, URIRef(str(ccp_ext) + 'A_' + str(a_hash))))
                    g.add((URIRef(str(ccp_ext) + 'A_' + str(a_hash)), RDF.type, FOAF.person))
                    g.add((URIRef(str(ccp_ext) + 'A_' + str(a_hash)), FOAF.familyName, Literal(str(author[0]))))
                    g.add((URIRef(str(ccp_ext) + 'A_' + str(a_hash)), FOAF.givenName, Literal(str(author[1]))))

                #create triples - article instances
                format_conversion_uri = base64.b64encode(hashlib.sha1(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_XML' + str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_TXT').digest())
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_XML'), RDF.type, URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]))))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_TXT'), RDF.type, URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]))))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_XML'), URIRef(str(swo) + 'SWO_0004002'), URIRef(str(edam) + 'format_2332')))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_XML'), URIRef(str(swo) + 'SWO_0000046'), Literal(str('/'.join(item.split('/')[:-1])) + '/PMC' + str(c_inf[0]) + '.nxml.gz')))
                g.add((URIRef(str(ccp_ext) + 'FC_' + str(format_conversion_uri)), URIRef(str(swo) + 'SWO_0000086'), URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_XML')))
                g.add((URIRef(str(ccp_ext) + 'FC_' + str(format_conversion_uri)), RDF.type, URIRef(str(edam) + 'operation_0335')))
                g.add((URIRef(str(ccp_ext) + 'FC_' + str(format_conversion_uri)), URIRef(str(swo) + 'SWO_0000087'), URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_TXT')))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_TXT'), URIRef(str(swo) + 'SWO_0004002'), URIRef(str(swo) + 'SWO_3000043')))
                g.add((URIRef(str(ccp_ext) + 'P_PMC_' + str(c_inf[0]) + '_TXT'), URIRef(str(swo) + 'SWO_0000046'), Literal(str('/'.join(item.split('/')[:-1])) + '/PMC' + str(c_inf[0]) + '.nxml.gz.txt.gz')))



    file_name = file_dir.split('/')[-1]
    out = str('/'.join(file_dir.split('/')[:-2])) + '/metadata_triples'
    g.serialize(destination=str(out) + '/PMC_metadata_' + str(file_name) + '.xml', format='turtle')

    print 'Completed ' + str(file_dir)



def main():

    # set default encoding to utf8
    reload(sys)
    sys.setdefaultencoding('utf8') # needed to parse article titles

    #specify initial arguments for all functions
    # dir_name = str(os.getcwd()) + '/oa_package'
    dir_name = "/RAID3/data/hudson/library/pmc_oa/2017/oa_package"
    file_dir = [str(dir_name) + '/' + str(x) for x in next(os.walk(dir_name))[1]]  # iterable for paralleling

    pool = multiprocessing.Pool(processes=5)  # set up pool
    triple = pool.map(TripleMaker, file_dir)

    #close and join pool
    pool.close()
    pool.join()


if __name__ == '__main__':
    main()


# #get citation count from doi
#from habanero import counts
# if dict2['doi']:
#     print counts.citation_count(doi=dict_out['doi'])
