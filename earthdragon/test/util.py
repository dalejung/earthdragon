def preamble():
    from earthdragon.typecheck import typecheck_enable
    typecheck_enable('earthdragon')

def run_in_place(func):
    func()
