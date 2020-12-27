#https://github.com/openhab/openhab-core/blob/master/bundles/org.openhab.core.semantics/model/SemanticTags.csv
from core.actions import HTTP
import json
import re
import io

from core import osgi,metadata
try:
    from org.openhab.core.items import Metadata, MetadataKey
except:
    from org.eclipse.smarthome.core.items import Metadata, MetadataKey
    
METADATA_REGISTRY = osgi.get_service(
    "org.openhab.core.items.MetadataRegistry"
) or osgi.get_service(
    "org.eclipse.smarthome.core.items.MetadataRegistry"
)

class SemanticItem:
    def __init__(self,item,semantic_type,semantic_properties,tags,synonyms,answer):
        self.item = item
        self.semantic_type = semantic_type
        self.semantic_properties = semantic_properties
        self.label = [item.getLabel().lower()] if item.getLabel() is not None else []
        self.tags = tags
        self.synonyms = synonyms
        self.answer = answer
        self.search_terms = list(set(self.label + self.synonyms + self.tags))

        self.children = []
        self.parents = []
        self.root_path = []
        
    def getItem(self):
        return self.item

    def getSemanticType(self):
        return self.semantic_type

    def getSemanticProperties(self):
        return self.semantic_properties

    def getSearchTerms(self):
        return self.search_terms

    def getAnswer(self):
        return self.answer

    def getChildren(self):
        return self.children
      
    def getParents(self):
        return self.parents

    def getRootPath(self):
        return self.root_path
      
    def __repr__(self):
        return self.item.getName() + " (" + str(self.label) + "|" + str(self.tags) + "|" + str(self.synonyms) + ")"

class SemanticModel:
    def test(self,log):
        #log.info(u"{}".format(self.semantic_items["pOther_Scene4"].answer))
        pass
      
    def __init__(self,item_registry,config):
        semantic_tags = {}
        f = io.open("/openhab/python/shared/semantic/config/tags_de.txt", "r", encoding="utf-8")
        lines = f.readlines()
        for line in lines:
            keys,synonyms = line.strip().split("=")
            keys = keys.split("_")
            synonyms = synonyms.lower().split(",")
            type = keys[0]
            name = keys[-1]
            
            semantic_tags[name] = [type,synonyms]

        semantic_tags["Location"] = ["Location",[]]
        semantic_tags["Equipment"] = ["Equipment",[]]
        semantic_tags["Point"] = ["Point",[]]
        semantic_tags["Property"] = ["Property",[]]

        # build semantic items
        self.semantic_items = {}
        for item in item_registry.getItems():
            semantic_type = "Group" if item.getType() == "Group" else "Item"
            semantic_properties = []
            tags_search = []
            item_tags = item.getTags()
            for item_tag in item_tags:
                if item_tag in semantic_tags:
                    _semantic_type,_tags_search = semantic_tags[item_tag]
                    tags_search += _tags_search
                    if _semantic_type in ["Location","Equipment","Point"]:
                        semantic_type = _semantic_type
                    elif _semantic_type == "Property":
                        semantic_properties.append(item_tag)
                  
            #[u'semantics', u'synonyms']
            synonyms = METADATA_REGISTRY.get(MetadataKey("synonyms", item.getName()))
            synonym_search = synonyms.getValue().lower().split(",") if synonyms is not None else []
            synonym_search = map(unicode.strip, synonym_search)
            
            answer = METADATA_REGISTRY.get(MetadataKey("answer", item.getName()))
            answer = answer.getValue() if answer is not None else None

            semantic_item = SemanticItem(item,semantic_type,semantic_properties,tags_search,synonym_search,answer)
            self.semantic_items[semantic_item.item.getName()] = semantic_item

        # prepare semantic locations and children
        self.root_locations = []
        for semantic_item in self.semantic_items.values():
            if semantic_item.item.getType() == "Group":
                children = semantic_item.item.getMembers()
                for item in children:
                    semantic_item.children.append(self.semantic_items[item.getName()])

                if semantic_item.getSemanticType() == "Location":
                    if len(semantic_item.item.getGroupNames()) == 0:
                        self.root_locations.append(semantic_item)
                        
        # prepare parents
        for semantic_item in self.semantic_items.values():
            for semantic_children in semantic_item.children:
                semantic_children.parents.append(semantic_item)

        # prepare root path
        for semantic_item in self.semantic_items.values():
            semantic_item.root_path = set(self.buildPathParents(semantic_item,[]))

        # prepare regex matcher
        self.semantic_search_part_regex = {}
        self.semantic_search_full_regex = {}
        for semantic_item in self.semantic_items.values():
            for search_term in semantic_item.search_terms:
                if search_term in self.semantic_search_part_regex:
                    continue
                self.semantic_search_part_regex[search_term] = re.compile(config["main"]["phrase_part_matcher"].format(search_term))
                self.semantic_search_full_regex[search_term] = re.compile(config["main"]["phrase_full_matcher"].format(search_term))
                
                
        search_terms = {}
        for semantic_item in self.semantic_items.values():
            semantic_type = semantic_item.getSemanticType()
            if semantic_type not in search_terms:
                search_terms[semantic_type] = {}
            for search_term in semantic_item.getSearchTerms():
                if search_term not in search_terms[semantic_type]:
                    search_terms[semantic_type][search_term] = []
                search_terms[semantic_type][search_term].append(semantic_item)
                
        # build search term maps for items with shared search terms
        # e.g. flur unten <=> wohnzimmer stehlampe unten
        self.children_search_map = {"Location": {},"Equipment": {}, "Point": {}}
        self.buildDuplicateSearchMap(search_terms,"Location","Equipment")
        self.buildDuplicateSearchMap(search_terms,"Location","Point")
        self.buildDuplicateSearchMap(search_terms,"Equipment","Point")

    def buildPathParents(self,semantic_item,parents=[]):
        parents.append(semantic_item)
        for parent in semantic_item.getParents():
            if parent in parents or parent.getSemanticType() == "Group":
                continue
            self.buildPathParents(parent,parents)
        return parents
      
    def buildDuplicateSearchMap(self,search_terms,semantic_parent_type,semantic_child_type):
        duplicate_search_terms = set(search_terms[semantic_parent_type].keys()) & set(search_terms[semantic_child_type].keys())
        for search_term in duplicate_search_terms:
            equipment_parents = []
            for semantic_equipment in search_terms[semantic_child_type][search_term]:
                for path_item in semantic_equipment.getRootPath():
                    if path_item.getSemanticType() != semantic_parent_type:
                        continue
                    if search_term not in self.children_search_map[semantic_parent_type]:
                        self.children_search_map[semantic_parent_type][search_term] = []
                    self.children_search_map[semantic_parent_type][search_term].append(path_item)
        for search_term in self.children_search_map[semantic_parent_type]:
            self.children_search_map[semantic_parent_type][search_term] = set(self.children_search_map[semantic_parent_type][search_term])
            
    def getSemanticItem(self,item_name):
        return self.semantic_items[item_name]
    
    def getSearchFullRegex(self,search_term):
        return self.semantic_search_full_regex[search_term]
      
    def getSearchPartRegex(self,search_term):
        return self.semantic_search_part_regex[search_term]
      
    def getRootLocations(self):
        return self.root_locations
      
    def getAlternativeChildrenPathMap(self,semantic_type):
        return self.children_search_map[semantic_type]
