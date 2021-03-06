from office365.runtime.client_result import ClientResult
from office365.runtime.queries.delete_entity_query import DeleteEntityQuery
from office365.runtime.queries.service_operation_query import ServiceOperationQuery
from office365.runtime.resource_path import ResourcePath
from office365.runtime.resource_path_service_operation import ResourcePathServiceOperation
from office365.sharepoint.changes.change_collection import ChangeCollection
from office365.sharepoint.changes.change_query import ChangeQuery
from office365.sharepoint.contenttypes.content_type_collection import ContentTypeCollection
from office365.sharepoint.fields.field_collection import FieldCollection
from office365.sharepoint.fields.related_field_collection import RelatedFieldCollection
from office365.sharepoint.files.checkedOutFileCollection import CheckedOutFileCollection
from office365.sharepoint.folders.folder import Folder
from office365.sharepoint.forms.form_collection import FormCollection
from office365.sharepoint.listitems.caml.caml_query import CamlQuery
from office365.sharepoint.listitems.listitem import ListItem
from office365.sharepoint.listitems.listItem_collection import ListItemCollection
from office365.sharepoint.permissions.securable_object import SecurableObject
from office365.sharepoint.views.view import View
from office365.sharepoint.views.view_collection import ViewCollection


class List(SecurableObject):
    """List resource"""

    def __init__(self, context, resource_path=None):
        super(List, self).__init__(context, resource_path)

    def save_as_template(self, fileName, name, description, saveData):
        """
        Saves the list as a template in the list template gallery and includes the option of saving with or
        without the data that is contained in the current list.

        :param bool saveData: true to save the data of the original list along with the list template; otherwise, false.
        :param str description: A string that contains the description for the list template.
        :param str name: A string that contains the title for the list template.
        :param str fileName: A string that contains the file name for the list template with an .stp extension.
        :return:
        """
        payload = {
            "strFileName": fileName,
            "strName": name,
            "strDescription": description,
            "bSaveData": saveData
        }
        qry = ServiceOperationQuery(self, "saveAsTemplate", None, payload, None, None)
        self.context.add_query(qry)
        return self

    def get_item_by_unique_id(self, uniqueId):
        """
        Returns the list item with the specified ID.

        :param str uniqueId:"""
        item = ListItem(self.context, ResourcePathServiceOperation("getItemByUniqueId", [uniqueId], self.resource_path))
        return item

    def get_web_dav_url(self, source_url):
        """
        Gets the trusted URL for opening the folder in Explorer view.

        :param str source_url: The URL of the current folder the user is in.
        :return: ClientResult
        """

        result = ClientResult(str)
        payload = {
            "sourceUrl": source_url
        }
        qry = ServiceOperationQuery(self, "getWebDavUrl", None, payload, None, result)
        self.context.add_query(qry)
        return result

    def get_items(self, caml_query=None):
        """Returns a collection of items from the list based on the specified query.
        :type caml_query: CamlQuery
        """
        if not caml_query:
            caml_query = CamlQuery.create_all_items_query()
        items = ListItemCollection(self.context, ResourcePath("items", self.resource_path))
        qry = ServiceOperationQuery(self, "GetItems", None, caml_query, "query", items)
        self.context.add_query(qry)
        return items

    def add_item(self, list_item_creation_information):
        """The recommended way to add a list item is to send a POST request to the ListItemCollection resource endpoint,
         as shown in ListItemCollection request examples.

         :type list_item_creation_information: ListItemCreationInformation or dict"""
        item = ListItem(self.context)
        if isinstance(list_item_creation_information, dict):
            for k, v in list_item_creation_information.items():
                item.set_property(k, v, True)
            self.items.add_child(item)
            item.ensure_type_name(self)
            qry = ServiceOperationQuery(self, "items", None, item, None, item)
            self.context.add_query(qry)
        else:
            def _resolve_folder_url():
                list_item_creation_information.FolderUrl = self.context.base_url + self.rootFolder.serverRelativeUrl
                add_item_qry = ServiceOperationQuery(
                    self,
                    "addItem",
                    None,
                    list_item_creation_information,
                    "parameters",
                    item
                )
                self.context.add_query(add_item_qry)

            self.rootFolder.ensure_property("ServerRelativeUrl", _resolve_folder_url)
        return item

    def get_item_by_id(self, item_id):
        """Returns the list item with the specified list item identifier.

        :type item_id: int
        """
        return ListItem(self.context,
                        ResourcePathServiceOperation("getItemById", [item_id], self.resource_path))

    def get_view(self, view_id):
        """Returns the list view with the specified view identifier.

        :type view_id: str
        """
        view = View(self.context, ResourcePathServiceOperation("getView", [view_id], self.resource_path), self)
        return view

    def get_changes(self, query=None):
        """Returns the collection of changes from the change log that have occurred within the list,
           based on the specified query.

        :param office365.sharepoint.changeQuery.ChangeQuery query: Specifies which changes to return
        """
        if query is None:
            query = ChangeQuery(list_=True)
        changes = ChangeCollection(self.context)
        qry = ServiceOperationQuery(self, "getChanges", None, query, "query", changes)
        self.context.add_query(qry)
        return changes

    def get_checked_out_files(self):
        result = CheckedOutFileCollection(self.context)
        qry = ServiceOperationQuery(self, "GetCheckedOutFiles", None, None, None, result)
        self.context.add_query(qry)
        return result

    def get_related_fields(self):
        """Returns a collection of lookup fields that use this list as a data source and
            that have FieldLookup.IsRelationship set to true.
        """
        return RelatedFieldCollection(self.context,
                                      ResourcePathServiceOperation("getRelatedFields", [], self.resource_path))

    def delete_object(self):
        """Deletes the list.

        :rtype: List
        """
        qry = DeleteEntityQuery(self)
        self.context.add_query(qry)
        self.remove_from_parent_collection()
        return self

    @property
    def enable_folder_creation(self):
        """
        Specifies whether new list folders can be added to the list.

        :rtype: bool or None
        """
        return self.properties.get("EnableFolderCreation", None)

    @enable_folder_creation.setter
    def enable_folder_creation(self, value):
        self.set_property("EnableFolderCreation", value, True)

    @property
    def items(self):
        """Get list items"""
        if self.is_property_available('Items'):
            return self.properties["Items"]
        else:
            return ListItemCollection(self.context, ResourcePath("items", self.resource_path))

    @property
    def rootFolder(self):
        """Get a root folder"""
        if self.is_property_available('RootFolder'):
            return self.properties["RootFolder"]
        else:
            return Folder(self.context, ResourcePath("RootFolder", self.resource_path))

    @property
    def fields(self):
        """Gets a value that specifies the collection of all fields in the list."""
        if self.is_property_available('Fields'):
            return self.properties['Fields']
        else:
            return FieldCollection(self.context, ResourcePath("Fields", self.resource_path), self)

    @property
    def views(self):
        """Gets a value that specifies the collection of all public views on the list and personal views
        of the current user on the list."""
        if self.is_property_available('Views'):
            return self.properties['Views']
        else:
            return ViewCollection(self.context, ResourcePath("views", self.resource_path), self)

    @property
    def defaultView(self):
        """Gets or sets a value that specifies whether the list view is the default list view."""
        if self.is_property_available('DefaultView'):
            return self.properties['DefaultView']
        else:
            return View(self.context, ResourcePath("DefaultView", self.resource_path), self)

    @property
    def contentTypes(self):
        """Gets the content types that are associated with the list."""
        if self.is_property_available('ContentTypes'):
            return self.properties['ContentTypes']
        else:
            return ContentTypeCollection(self.context,
                                         ResourcePath("contenttypes", self.resource_path))

    @property
    def forms(self):
        """Gets a value that specifies the collection of all list forms in the list."""
        return self.properties.get('Forms',
                                   FormCollection(self.context, ResourcePath("forms", self.resource_path)))

    @property
    def parentWeb(self):
        """Gets a value that specifies the web where list resides."""
        from office365.sharepoint.webs.web import Web
        return self.properties.get('ParentWeb',
                                   Web(self.context, ResourcePath("parentWeb", self.resource_path)))

    @property
    def item_count(self):
        """Gets a value that specifies the number of list items in the list.
        :rtype: int or None
        """
        return self.properties.get('ItemCount', None)

    @property
    def title(self):
        """Gets the displayed title for the list.
        :rtype: str or None
        """
        return self.properties.get('Title', None)

    @title.setter
    def title(self, val):
        """Sets the displayed title for the list."""
        self.set_property('Title', val)

    @property
    def description(self):
        """Gets the description for the list.
        :rtype: str or None
        """
        return self.properties.get('Description', None)

    @description.setter
    def description(self, val):
        """Sets the description for the list."""
        self.set_property('Description', val)

    def set_property(self, name, value, persist_changes=True):
        super(List, self).set_property(name, value, persist_changes)
        # fallback: create a new resource path
        if self._resource_path is None:
            if name == "Id":
                self._resource_path = ResourcePathServiceOperation(
                    "GetById", [value], self._parent_collection.resource_path)
            elif name == "Title":
                self._resource_path = ResourcePathServiceOperation(
                    "GetByTitle", [value], self._parent_collection.resource_path)
        return self
