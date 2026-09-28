

def check(timing_report):
    '''
    Purpose:  This rule checks the starting clock point is the same between the data path and the required path.
    '''

    data_path_start = timing_report.data_path.delays[0].resource    
    required_path_start = timing_report.required_path.delays[0].resource    

    if data_path_start != required_path_start:
        return False
    return True
