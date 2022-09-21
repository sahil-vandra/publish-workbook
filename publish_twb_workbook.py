import argparse
import tableauserverclient as TSC


def main(args):
    print('\nworkbooks filepath::', args.workbook_files)

    wb_list = []
    for wb in args.workbook_files.split(","):
        temp_wb = wb.strip()
        if len(temp_wb) > 0:
            wb_list.append(temp_wb)
    print("\nwb_list::", wb_list)

    if len(wb_list) > 0:
        # Step 1: Sign in to server.
        tableau_auth = TSC.TableauAuth(args.username, args.password)
        server = TSC.Server(args.server_url)
        overwrite_true = TSC.Server.PublishMode.Overwrite

        with server.auth.sign_in(tableau_auth):
            # Step 3: New workbook item publish.
            for wb_file in wb_list:
                new_workbook = TSC.WorkbookItem(args.project_id)
                new_workbook = server.workbooks.publish(
                    new_workbook, wb_file, overwrite_true)
                print(f"\nWorkbook :: {wb_file} :: published")
    else:
        print("Workbook list is null")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--username', action='store',
                        type=str, required=True)
    parser.add_argument('--password', action='store',
                        type=str, required=True)
    parser.add_argument('--server_url', action='store',
                        type=str, required=True)
    parser.add_argument('--project_id', action='store',
                        type=str, required=True)
    parser.add_argument('--workbook_files', action='store',
                        type=str, required=True)
    args = parser.parse_args()
    main(args)

# python3 publish_twb_workbook.py --username 'Nirav.Padia' --password 'Password1' --server_url 'https://tableau.devinvh.com/' --project_id '40e18c1e-6926-4ca5-bf10-82a8b8d89e27' --workbook_files '/home/dev1003/workbook files/Sample.twb,/home/dev1003/workbook files/Sample - Superstore.twb,/home/dev1003/workbook files/Sample.twbx,/home/dev1003/workbook files/Sales Growth Dashboard.twbx,/home/dev1003/workbook files/InsideAirbnb.twbx'