import sqlite3
c=sqlite3.connect(r'%USERPROFILE%/.agents/skills/civ6-modding/database/api.sqlite').cursor()
for r in c.execute("SELECT func_name, table_name, availability, args_flat, description FROM api_functions WHERE func_name LIKE '%SendLuaEvent%' OR table_name LIKE '%ReportingEvents%'"):
    print('SendLuaEvent | table=',r[1],'| av=',r[2],'| args=',r[3],'|',str(r[4])[:80])
