import argparse
import logging
import tableauserverclient as TSC


def main(args):
    logging.basicConfig(level=40)
    print('\nfilepath::', args.filepath) # ",Sample - Superstore.twb ,Sample.twb"
    workbook_file_list = []

    temp_workbook_file_list = args.filepath.split(",")
    for i in temp_workbook_file_list:
        a = i.strip()
        if len(a) > 0:
            workbook_file_list.append(a)
    print("\nworkbook_file_list::", workbook_file_list)
    
    if len(workbook_file_list) > 0:
        # Step 1: Sign in to server.
        tableau_auth = TSC.TableauAuth(args.username, args.password)
        server = TSC.Server('https://tableau.devinvh.com/')
        overwrite_true = TSC.Server.PublishMode.Overwrite

        with server.auth.sign_in(tableau_auth):
            # Step 2: Get all the projects on server, then look for the default one.
            all_projects, pagination_item = server.projects.get()
            project = next(
                (project for project in all_projects if project.name == args.project_name), None)
            # Step 3: If default project is found, form a new workbook item and publish.
            if project is not None:
                for file in workbook_file_list:
                    new_workbook = TSC.WorkbookItem(project.id)
                    new_workbook = server.workbooks.publish(
                        new_workbook, file, overwrite_true)
                    print("Workbook published.")
            else:
                error = "The project could not be found."
                raise LookupError(error)
    else: print("Workbook list is null")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        '--username', '-u', help='username to sign into server')
    parser.add_argument(
        '--password', '-f', help='filepath to the workbook to publish')
    parser.add_argument('--filepath', help='filepath to the workbook to publish', type=str, action='store_true')
    parser.add_argument('--project_name', action='store',
                        type=str)

    args = parser.parse_args()
    main(args)
