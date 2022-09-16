import argparse
import logging
import tableauserverclient as TSC


def main(args):
    print('\nfilepath::', args.filepath)
    logging.basicConfig(level=40)
    
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
            new_workbook = TSC.WorkbookItem(project.id)
            new_workbook = server.workbooks.publish(
                new_workbook, args.filepath, overwrite_true)
            print("Workbook published.")
        else:
            error = "The project could not be found."
            raise LookupError(error)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        '--username', '-u', help='username to sign into server', default='Nirav.Padia')
    parser.add_argument(
        '--password', '-f', help='filepath to the workbook to publish', default='Password1')
    parser.add_argument('--filepath', help='filepath to the workbook to publish',
                        default='/home/dev1003/OneDrive/sahilvandra.softvan@gmail.com/IH/publish twb and twbx workbook using python rest api/Sample - Superstore.twb')
    parser.add_argument('--project_name', action='store',
                        type=str, default="Technology")

    args = parser.parse_args()
    main(args)
