import copy
import uuid
from datetime import datetime


class MockFlexilims:
    def __init__(self, project_id=None):
        self.project_id = project_id
        self.data = {}  # Stores entities by id
        self.indices = {}  # Stores entities by datatype

    def _generate_id(self):
        return str(uuid.uuid4())

    def get(self, datatype, **kwargs):
        """
        Mock get method.
        Supports filtering by attributes passed in kwargs.
        """
        results = []
        if datatype not in self.indices:
            return []

        for entity_id in self.indices[datatype]:
            entity = self.data[entity_id]
            match = True
            for key, value in kwargs.items():
                if value is None:
                    continue
                if key == "id":
                    if entity["id"] != value:
                        match = False
                        break
                elif key == "name":
                    if entity["name"] != value:
                        match = False
                        break
                elif key in entity["attributes"]:
                    if entity["attributes"][key] != value:
                        match = False
                        break
                else:
                    # Key not found in attributes or top-level fields
                    match = False
                    break

            if match:
                # Return a deep copy to prevent in-place modifications by
                # format_results from corrupting the store
                results.append(copy.deepcopy(entity))

        return results

    def post(
        self,
        datatype,
        name,
        attributes=None,
        origin_id=None,
        other_relations=None,
        strict_validation=False,
        id=None,
    ):
        """
        Mock post method.
        """
        if attributes is None:
            attributes = {}

        # Check for duplicates if name is provided
        existing = self.get(datatype, name=name)
        if existing:
            # In real flexilims this might raise an error or return existing,
            # but here we'll simulate a basic post that creates a new one if
            # it doesn't exist or raises if it does (mimicking the
            # "NameNotUnique" behavior usually seen).
            # However, looking at data_for_testing, it seems to expect
            # successful creation. Let's assume for now we just create it.
            pass

        new_id = id if id else self._generate_id()

        # Ensure attributes is a dictionary and copy it to avoid reference issues
        final_attributes = attributes.copy() if attributes else {}

        # Handle genealogy if not present but origin exists
        if "genealogy" not in final_attributes and origin_id:
            origin = self.data.get(origin_id)
            if origin:
                origin_genealogy = origin["attributes"].get("genealogy", [])
                final_attributes["genealogy"] = list(origin_genealogy) + [name]

        entity = {
            "id": new_id,
            "name": name,
            "datatype": datatype,
            "project_id": self.project_id,
            "project": self.project_id,
            "attributes": final_attributes,
            "created_at": datetime.now().isoformat(),
            "created_by": "mock_user",
            "origin_id": origin_id,
        }

        self.data[new_id] = entity
        if datatype not in self.indices:
            self.indices[datatype] = []
        self.indices[datatype].append(new_id)

        return entity

    def update(self, datatype, name, id, attributes=None, **kwargs):
        if id in self.data:
            if attributes:
                self.data[id]["attributes"].update(attributes)
            return self.data[id]
        return None

    def delete(self, id):
        if id in self.data:
            entity = self.data[id]
            datatype = entity["datatype"]
            del self.data[id]
            if datatype in self.indices:
                self.indices[datatype].remove(id)
            return True
        return False

    def update_one(
        self,
        datatype,
        id,
        name=None,
        origin_id=None,
        attributes=None,
        strict_validation=False,
    ):
        return self.update(datatype, name, id, attributes)

    def get_children(self, parent_id):
        """
        Get all children of a parent entity.
        """
        children = []
        for entity in self.data.values():
            if entity.get("origin_id") == parent_id:
                # Return a copy and add 'type' alias for 'datatype'
                child = copy.deepcopy(entity)
                child["type"] = child["datatype"]
                children.append(child)
        return children
