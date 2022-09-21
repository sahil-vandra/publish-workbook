import tableauserverclient as TSC


def main():
    # Step 1: Sign in to server.
    tableau_auth = TSC.TableauAuth('Nirav.Padia', 'Password1')
    server = TSC.Server('https://tableau.devinvh.com/')

    with server.auth.sign_in(tableau_auth):
        # create a workbook item
        wb_item = TSC.WorkbookItem(project_id='40e18c1e-6926-4ca5-bf10-82a8b8d89e27')
        # call the publish method with the workbook item
        wb_item = server.workbooks.publish(wb_item, 'Sample - Superstore.twb', 'Overwrite')

if __name__ == '__main__':
    main()
