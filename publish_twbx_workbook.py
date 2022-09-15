import argparse
import requests
import xml.etree.ElementTree as ET
import os
import math

from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata

xmlns = {'t': 'http://tableau.com/api'}
FILESIZE_LIMIT = 1024 * 1024 * 64   # 64MB
CHUNK_SIZE = 1024 * 1024 * 20    # 20MB


class ApiCallError(Exception):
    pass


class UserDefinedFieldError(Exception):
    pass


def _encode_for_display(text):
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')


def _make_multipart(parts):
    mime_multipart_parts = []
    for name, (filename, blob, content_type) in parts.items():
        multipart_part = RequestField(name=name, data=blob, filename=filename)
        multipart_part.make_multipart(content_type=content_type)
        mime_multipart_parts.append(multipart_part)

    post_body, content_type = encode_multipart_formdata(mime_multipart_parts)
    content_type = ''.join(('multipart/mixed',) +
                           content_type.partition(';')[1:])
    return post_body, content_type


def _check_status(server_response, success_code):
    if server_response.status_code != success_code:
        parsed_response = ET.fromstring(server_response.text)

        # Obtain the 3 xml tags from the response: error, summary, and detail tags
        error_element = parsed_response.find('t:error', namespaces=xmlns)
        summary_element = parsed_response.find(
            './/t:summary', namespaces=xmlns)
        detail_element = parsed_response.find('.//t:detail', namespaces=xmlns)

        # Retrieve the error code, summary, and detail if the response contains them
        code = error_element.get(
            'code', 'unknown') if error_element is not None else 'unknown code'
        summary = summary_element.text if summary_element is not None else 'unknown summary'
        detail = detail_element.text if detail_element is not None else 'unknown detail'
        error_message = '{0}: {1} - {2}'.format(code, summary, detail)
        raise ApiCallError(error_message)
    return


def sign_in(server, username, password, site=""):
    url = server + "/api/3.15/auth/signin"

    # Builds the request
    xml_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(
        xml_request, 'credentials', name=username, password=password)
    ET.SubElement(credentials_element, 'site', contentUrl=site)
    xml_request = ET.tostring(xml_request)

    # Make the request to server
    server_response = requests.post(url, data=xml_request)
    _check_status(server_response, 200)

    # ASCII encode server response to enable displaying to console
    server_response = _encode_for_display(server_response.text)

    # Reads and parses the response
    parsed_response = ET.fromstring(server_response)

    # Gets the auth token and site ID
    token = parsed_response.find(
        't:credentials', namespaces=xmlns).get('token')
    site_id = parsed_response.find('.//t:site', namespaces=xmlns).get('id')
    return token, site_id


def sign_out(server, auth_token):
    url = server + "/api/3.15/auth/signout"
    server_response = requests.post(
        url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)
    return


def start_upload_session(server, auth_token, site_id):
    url = server + "/api/3.15/sites/{0}/fileUploads".format(site_id)
    server_response = requests.post(
        url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 201)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    return xml_response.find('t:fileUpload', namespaces=xmlns).get('uploadSessionId')


def get_project_id(server, auth_token, site_id, project_name):
    page_num, page_size = 1, 100  # Default paginating values

    # Builds the request
    url = server + "/api/3.15/sites/{0}/projects".format(site_id)
    paged_url = url + \
        "?pageSize={0}&pageNumber={1}".format(page_size, page_num)
    server_response = requests.get(
        paged_url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    # Used to determine if more requests are required to find all projects on server
    total_projects = int(xml_response.find(
        't:pagination', namespaces=xmlns).get('totalAvailable'))
    max_page = int(math.ceil(total_projects / page_size))
    projects = xml_response.findall('.//t:project', namespaces=xmlns)

    # Continue querying if more projects exist on the server
    for page in range(2, max_page + 1):
        paged_url = url + \
            "?pageSize={0}&pageNumber={1}".format(page_size, page)
        server_response = requests.get(
            paged_url, headers={'x-tableau-auth': auth_token})
        _check_status(server_response, 200)
        xml_response = ET.fromstring(_encode_for_display(server_response.text))
        projects.extend(xml_response.findall('.//t:project', namespaces=xmlns))

    # Look through all projects to find the mensioned project id
    for project in projects:
        if project.get('name') == project_name:
            return project.get('id')
    raise LookupError("Project named was not found on server")


def main(args):
    workbook_file_list = []
    server = 'https://tableau.devinvh.com'

    temp_workbook_file_list = args.workbook_files.split(",")
    for i in temp_workbook_file_list:
        a = i.strip()
        if len(a) > 0:
            workbook_file_list.append(a)
    print("\nworkbook_file_list::", workbook_file_list)

    ##### STEP 1: SIGN IN #####
    print("\n1. Signing in as " + args.username)
    auth_token, site_id = sign_in(server, args.username, args.password)

    ##### STEP 2: OBTAIN PROJECT ID #####
    print("\n2. Finding project to publish")
    project_id = get_project_id(
        server, auth_token, site_id, args.project_name)
    print("\nproject_id ::", project_id)

    # for workbook_file_path,  workbook_file in zip(workbook_file_path_list, workbook_file_list):
    for workbook_file in workbook_file_list:
        print("\nworkbook_file ::", workbook_file)

        print(
            "\n*Publishing '{0}' to the project as {1}*".format(workbook_file, args.username))

        # Break workbook file by name and extension
        workbook_filename, file_extension = workbook_file.split('.', 1)

        if file_extension != 'twbx':
            error = "This sample only accepts .twbx files to publish. More information in file comments."
            raise UserDefinedFieldError(error)

        # Get workbook size to check if chunking is necessary
        workbook_size = os.path.getsize(workbook_file)
        print("\nworkbook_size:", workbook_size)
        chunked = workbook_size >= FILESIZE_LIMIT
        
        ##### STEP 3: PUBLISH WORKBOOK ######
        # Build a general request for publishing
        xml_request = ET.Element('tsRequest')
        workbook_element = ET.SubElement(
            xml_request, 'workbook', name=workbook_filename)
        ET.SubElement(workbook_element, 'project', id=project_id)
        xml_request = ET.tostring(xml_request)

        print("\nchunked :", chunked)
        if chunked:
            print("\n3. Publishing '{0}' in {1}MB chunks (workbook over 64MB)".format(
                workbook_file, CHUNK_SIZE / 1024000))
            # Initiates an upload session
            uploadID = start_upload_session(server, auth_token, site_id)

            # URL for PUT request to append chunks for publishing
            put_url = server + \
                "/api/3.15/sites/{0}/fileUploads/{1}".format(site_id, uploadID)

            # Read the contents of the file in chunks of 100KB
            with open(workbook_file, 'rb') as f:
                while True:
                    data = f.read(CHUNK_SIZE)
                    if not data:
                        break

                    payload, content_type = _make_multipart({'request_payload': ('', '', 'text/xml'),
                                                            'tableau_file': ('file', data, 'application/octet-stream')})
                    print("\tPublishing a chunk...")
                    server_response = requests.put(put_url, data=payload,
                                                   headers={'x-tableau-auth': auth_token, "content-type": content_type})
                    _check_status(server_response, 200)

            # Finish building request for chunking method
            payload, content_type = _make_multipart(
                {'request_payload': ('', xml_request, 'text/xml')})

            publish_url = server + \
                "/api/3.15/sites/{0}/workbooks".format(site_id)
            publish_url += "?uploadSessionId={0}".format(uploadID)
            publish_url += "&workbookType={0}&overwrite=true".format(
                file_extension)
        else:
            print("\n3. Publishing '" + workbook_file +
                  "' using the all-in-one method (workbook under 64MB)")

            # Read the contents of the file to publish
            with open(workbook_file, 'rb') as f:
                workbook_bytes = f.read()

            # Finish building request for all-in-one method
            parts = {'request_payload': ('', xml_request, 'text/xml'),
                     'tableau_workbook': (workbook_file, workbook_bytes, 'application/octet-stream')}
            payload, content_type = _make_multipart(parts)

            publish_url = server + \
                "/api/3.15/sites/{0}/workbooks".format(site_id)
            publish_url += "?workbookType={0}&overwrite=true".format(
                file_extension)

        # Make the request to publish and check status code
        print("\tUploading...")
        server_response = requests.post(publish_url, data=payload,
                                        headers={'x-tableau-auth': auth_token, 'content-type': content_type})
        _check_status(server_response, 201)

    ##### STEP 4: SIGN OUT #####
    print("\n4. Signing out, and invalidating the authentication token")
    sign_out(server, auth_token)
    auth_token = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--workbook_files', action='store',
                        type=str, required=True)
    parser.add_argument('--project_name', action='store',
                        type=str, required=True)
    parser.add_argument('--password', action='store',
                        type=str, required=True)
    parser.add_argument('--username', action='store',
                        type=str, required=True)
    args = parser.parse_args()

    main(args)
