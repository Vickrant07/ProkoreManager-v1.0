import urllib
import requests
import sys
import pathlib

class ProcoreException(Exception):
    """
    The base exception class for Procore.
    Parameters:
        msg (str): Short description of the error.
        response: Error response from the API call.
    """

    def __init__(self, msg, response=None):
        super(ProcoreException, self).__init__(msg)
        self.message = msg
        self.response = response

    def __str__(self):
        return repr(self.message)


class NotFoundClientError(ProcoreException):
    """Client not found OAuth2 authorization, 404 error."""
    pass


class UnauthorizedClientError(ProcoreException):
    """Wrong client secret and/or refresh token, 401 error."""
    pass


class ExpiredTokenError(ProcoreException):
    """Expired (old) access token, 498 error."""
    pass


class InvalidTokenError(ProcoreException):
    """Wrong/non-existing access token, 401 error."""
    pass


class NoPrivilegeError(ProcoreException):
    """The user has insufficient privilege, 403 error."""
    pass


class WrongParamsError(ProcoreException):
    """Some of the parameters (HTTP params or request body) are wrong, 400 error."""
    pass


class NotFoundItemError(ProcoreException):
    """Not found the item from URL, 404 error."""
    pass
    

class InternalServerError(ProcoreException):
    """The rest Procore errors, 500 error."""
    pass

def raise_exception(response):
    """
    Raises an exception based on the provided status code

    Parameters
    ----------
    status_code : int
        valid get/request code
    """
    if response.status_code == 401:
        raise UnauthorizedClientError('Wrong client secret or/and refresh token', response.text)

    elif response.status_code == 404:
        raise NotFoundClientError('Client ID doesn\'t exist', response.text)

    elif response.status_code == 500:
        raise InternalServerError('Internal server error', response.text)

    else:
        raise ProcoreException('Error: {0}'.format(response.status_code), response.text)

class Base:
    """
    Base class for Procore API access
    """
    
    def __init__(self, access_token, server_url) -> None:
        """
        Initializes important API access parameters

        Creates
        -------
        __access_token : str
            token to access Procore resources
        __server_url : str
            base url to send GET/POST requests
        """
        self.__access_token = access_token
        self.__server_url = server_url

    def get_request(self, api_url, additional_headers=None, params=None):
        """
        Create a HTTP Get request

        Parameters
        ----------
        api_url : str
            endpoint for the specific API call
        additional_headers : dict, default None
            additional headers beyond Authorization
        params : dict, default None
            GET parameters to parse

        Returns
        -------
        response : dict
            GET response in json
        """
        if params is None:
            url = self.__server_url + api_url
        else:
            url = self.__server_url + api_url + "?" + urllib.parse.urlencode(params)

        headers = {"Authorization": f"Bearer {self.__access_token}"}
        if additional_headers is not None:
            for key, value in additional_headers.items():
                headers[key] = value

        response = requests.get(url, headers=headers)
        
        if response.ok:
            return response.json()
        else:
            raise_exception(response)

    def post_request(self, api_url, additional_headers=None, params=None, data=None, files=None):
        """
        Create a HTTP Get request

        Parameters
        ----------
        api_url : str
            endpoint for the specific API call
        additional_headers : dict, default None
            additional headers beyond Authorization
        data : dict, default None
            POST data to send
        files : list of tuple, default None
            open files to send to Procore

        Returns
        -------
        response : HTTP response object
            GET response details in json
        """
        # Get URL
        if params is None:
            url = self.__server_url + api_url
        else:
            url = self.__server_url + api_url + "?" + urllib.parse.urlencode(params)

        # Get Headers
        headers = {"Authorization": f"Bearer {self.__access_token}"}
        if additional_headers is not None:
            for key, value in additional_headers.items():
                headers[key] = value

        # Make the request with file if necessary
        if files is None:
            response = requests.post(
                url,
                headers=headers,
                json=data # use json for folder creation
            )
        else:
            response = requests.post(
                url,
                headers=headers,
                data=data, # use data for file creation
                files=files
            )
        
        if response.ok:
            return response.json()
        else:
            raise_exception(response)

    def patch_request(self, api_url, additional_headers=None, params=None, data=None, files=False):
        """
        Create a HTTP PATCH request

        Parameters
        ----------
        api_url : str
            endpoint for the specific API call
        additional_headers : dict, default None
            additional headers beyond Authorization
        params : dict, default None
            PATCH parameters to parse
        data : dict, default None
            POST data to send
        files : dict or boolean, default False
            False - updating folder so use json request
            True - updating file, but no file to include
            dict - updating file with new document

        Returns
        -------
        response : HTTP response object
            PATCH response details in json
        """
        # Get URL
        if params is None:
            url = self.__server_url + api_url
        else:
            url = self.__server_url + api_url + "?" + urllib.parse.urlencode(params)

        # Get Headers
        headers = {"Authorization": f"Bearer {self.__access_token}"}
        if additional_headers is not None:
            for key, value in additional_headers.items():
                headers[key] = value
        
        if files is False:
            response = requests.patch(
                url,
                headers=headers,
                json=data # json for folder update
            )
        elif files is True:
            response = requests.patch(
                url,
                headers=headers,
                data=data, # data for file update
            )
        else:
            response = requests.patch(
                url,
                headers=headers,
                data=data, # data for file update
                files=files
            )

        if response.ok:
            return response.json()
        else:
            raise_exception(response)
    
    def delete_request(self, api_url, additional_headers=None, params=None):
        """
        Execute a HTTP DELETE request

        Parameters
        ----------
        api_url : str
            endpoint for the specific API call
        additional_headers : dict, default None
            additional headers beyond Authorization
        params : dict, default None
            DELETE parameters to parse

        Returns
        -------
        response : HTTP response object
            DELETE response details in json
        """
        # Get URL
        if params is None:
            url = self.__server_url + api_url
        else:
            url = self.__server_url + api_url + "?" + urllib.parse.urlencode(params)

        # Get Headers
        headers = {"Authorization": f"Bearer {self.__access_token}"}
        if additional_headers is not None:
            for key, value in additional_headers.items():
                headers[key] = value

        # DELETE request
        response = requests.delete(
            url=url,
            headers=headers,
        )

        if response.ok:
            return {"status_code":response.status_code}
        else:
            raise_exception(response)


sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent}")


class Projects(Base):
    """
    Access and working with projects from a given company
    """

    def __init__(self, access_token, server_url) -> None:
        super().__init__(access_token, server_url)

        self.endpoint = "/rest/v1.1/projects"

    def get(self, company_id, per_page=100):
        """
        Gets a list of all the projects from a certain company

        Parameters
        ----------
        company_id : int
            unique identifier for the company
        per_page : int, default 100
            number of companies to include

        Returns
        -------
        projects : list of dict
            list where each value is a dict with the project's id, active status (is_active), and name
        """
        projects = []
        n_projects = 1
        page = 1
        while n_projects > 0:
            params = {
                "company_id": company_id,
                "page": page,
                "per_page": per_page
            }
            
            projects_per_page = self.get_request(
                api_url=self.endpoint,
                params=params
            )
            n_projects = len(projects_per_page)

            projects += projects_per_page

            page += 1

        return projects

    def find(self, company_id, identifier):
        """
        Finds a project based on the identifier

        Parameters
        ----------
        company_id : int
            company id that the project is under
        identifier : int or str
            project id number or company name
        
        Returns
        -------
        project : dict
            project-specific dictionary
        """
        if isinstance(identifier, int):
            key = "id"
        else:
            key = "name"

        for project in self.get(company_id=company_id):
            if project[key] == identifier:
                return project

        raise NotFoundItemError(f"Could not find project {identifier}")
