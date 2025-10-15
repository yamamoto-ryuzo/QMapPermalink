from qmap_permalink.qmap_webmap_generator import QMapWebMapGenerator
wg = QMapWebMapGenerator()
html = wg.generate_wms_based_html_page({'x':0,'y':0,'scale':10000,'themes':['A','B','C'],'bookmarks':[{'name':'b1','x':0,'y':0}]},800,600,8089)
print(html[:2000])  # first 2000 chars