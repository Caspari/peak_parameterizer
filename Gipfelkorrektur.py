# Script author: Stefan Rieder 2012

import os
import math
import csv
import datetime
import grass.script as grass
import grass.script.setup as gsetup
gisbase = os.environ["GISBASE"]
gisdbase = "E:/aGIS/grassdata/"
location = "newLocation"
mapset = "PERMANENT"
gsetup.init(gisbase, gisdbase, location, mapset)
print grass.read_command("g.version", flags="c")  

"""
Definiere Variablen
"""
# Werte muessen je nach Eingabetabelle geaendert werden. Bei 0 anfangen zu zaehlen!
x=3
y=4

gipfel = []
ergebnisausgabe = []

datei=csv.reader(open("immenstadt.csv", "rb"), delimiter = ";")
datei.next()
for row in datei:
    gipfel.append(row)

# Lese DGM ein
grass.read_command("r.in.gdal", input="E:/aGIS/Allgaeu_Daten/ASTGTM/ASTGTM2_N47E010_dem.tif", output="DGM", title="DGM", flags="oe", quiet="TRUE", overwrite="TRUE")
grass.read_command("g.region", rast="DGM")
# Smoothe DGM
#grass.read_command("r.neighbors", overwrite="TRUE", input="DGM", output="DGM_smooth", size="5")


"""
Invertiere DGM
An dieser STelle wird das digitale Gelaendemodell invertiert, d.h. der hoechste Wert wird zum niedrigsten und umgekehrt.
Dadurch entstehen aus Bergen Senken, in denen sich Wasser sammeln kann (fuer Gipfelkorrektur notwendig!)
"""
grass.run_command("r.mapcalc", **{"dgm_invert": "0-DGM"})


"""
Beginne die Schleife, in welcher die Gipfelkorrektur vorgenommen wird.
Annahme: Die "falsche" Koordinate befindet sich am richtigen Berghang.
Vorgehen: Von der "falschen" Koordinate wird Wasser fliessen gelassen, dass naturgemaess bergab fliesst. Durch das zuvor invertierte
digitale Gelaendemodell sammelt sich das Wasser nun also in den Senken (eigentlich Gipfel!). Somit wird die exakte Lage der DGM-Gipfel 
auf recht einfache Weise bestimmt.
"""
i = 0
while i<len(gipfel):
    ta = datetime.datetime.now()
    name = gipfel [i][1]
    xg = gipfel [i][x]
    yg = gipfel [i][y]
    print "Name=", name, "X=", xg, "Y=", yg
    
    
    """
    r.drain laesst Wasser von einem bestimmten Punkt aus fliessen und erstellt ein neues Rasterbild, in dem sich nur durchflossene Pixel 
    befinden. Der Parameter "c" sorgt dafuer, dass die Werte des Eingaberasters (negative Hoehenwerte) in dem neu erstellten Bild 
    uebernommen werden.
    """
    # DGM vorher ausschneiden?!
    grass.read_command("r.drain", flags="c", overwrite="TRUE",quiet="TRUE", input="dgm_invert", output="flowpath%s"%(i), coordinate="%s, %s" %(xg,yg))
        
    """
    Nun werden der maximale und der minimale Wert des Fliesspfades abgefragt. Der Pixel mit dem kleinsten Wert (= hoechster Punkt in
    richtigem DGM) ist somit der Gipfel des betrachteten Berges. Aus der Textausgabe wird dieser Wert schliesslich noch extrahiert und 
    mit -1 multipliziert, um die korrekte Hoehe des Berges zu bekommen.
    """
    bk=grass.read_command("r.info", flags="r", map="flowpath%s"%(i), quiet="TRUE")
    bk1=bk.rsplit('max=',1)[0]
    bk2=int(bk1.rsplit('=',2)[1])
    bk3 = bk2*-1
    print "DGM-Hoehe des Berges:", bk3
    
    """
    Nun wird das Rasterbild mit den Fliesspixeln reklassifiziert, damit dieses nur noch aus einem Pixel, dem korrekten DGM-Gipfel
    besteht. Dazu wird in diesem Abschnitt zuerst eine Datei mit Reklassifizierungsregeln erstellt. Alle Werte bis zur negativen Gipfelhoehe 
    erhalten den richtigen Gipfelwert (kleinere Werte als negative Gipfelhoehe kann es nicht geben). Alle groesseren Werte werden mit NULL
    beschrieben.
    """
    bk4 = str(bk2)
    bk5 = str(bk3)
    classes=file("E:/aGIS/grassdata/reclass_korrektur/bergkorrektur%s.0"%(i), "w")
    classes.write("-9999 thru ")
    classes.write(bk4) 
    classes.write("=")
    classes.write(bk5)
    classes.write("\n")
    classes.write(bk5)
    classes.write(" thru 9999 = NULL")
    classes.close()
    
    """
    r.reclass reklassifiziert das Bild mit den soeben erstellten und oben beschriebenen Reklassifizierungsregeln.
    """
    grass.read_command ("r.reclass", input="flowpath%s"%(i),
                    output="flowpath_reclass",
                    rules="E:/aGIS/grassdata/reclass_korrektur/bergkorrektur%s.0"%(i),
                    overwrite="TRUE",
                    quiet="TRUE")
    
      
    """
    Das reklassifizierte Rasterbild (mit nur einem Pixel) wird in diesem Schritt in ein Vektorformat konvertiert. Es entsteht ein "Polypunkt.Bild" mit nur einem Feature, 
    welches der korrigierte Gipfel ist.
    """
    print "Konvertiere Raster zu Vektor"
    grass.read_command("r.to.vect", input="flowpath_reclass", output="flowpath_vector", feature="point", flags="v", overwrite="TRUE", quiet="TRUE")
    print "Raster erfolreich zu Vektor konvertiert"
    
    """
    Um weitere Vorgaenge moeglichst variabel zu gestalten, wurde entschieden sich die Werte ausgeben zu lassen und in eine Tabelle zu schreiben. 
    In diesem Schritt werden mit v.info die Eigenschaften der Vektordatei abgefragt. Da nur ein Feature vorhanden ist, laesst sich so die Lage dessen sehr leicht
    bestimmen. Da die Ausgabe allerdings recht umfangreich ist, nimmt die Extrahierung der Koordinaten aus der Textazsgabe mehrere Befehle in Anspruch.
    """
    bxy=grass.read_command("v.info", map="flowpath_vector")
    
    """
    # Suchen der Koordinaten aus WGS84-Ausgabe
    bxy1=bxy[bxy.rfind('N:'):]
    bxy2=bxy1[:bxy1.rfind('E:')]
    bxy3=bxy2.rsplit('N',4)[1]
    bxy4=bxy3[bxy3.rfind(" "):]
    bxy5=bxy4.rsplit(':',2)[1]
    bxy6=bxy4.rsplit(':',1)[1]
    bxy7=bxy4.rsplit(':',1)[0]
    bxy8=bxy7.rsplit(' ',2)[1]
    bxy9=bxy8[:bxy8.rfind(":")]
    by=bxy9,".",bxy5,bxy6
    by1="".join(by)
    by_korr=float(by1)
    bxy1=bxy[bxy.rfind('E:'):]
    bxy2=bxy1[:bxy1.rfind('W:')]
    bxy3=bxy2.rsplit('E',1)[0]
    bxy4=bxy3[bxy3.rfind(' '):]
    bxy5=bxy4.rsplit(':',2)[1]
    bxy6=bxy4.rsplit(':',1)[1]
    bxy8=bxy4.rsplit(' ',2)[1]
    bxy9=bxy8.rsplit(':',2)[0]
    bx=bxy9,".",bxy5,bxy6
    bx1="".join(bx)
    bx_korr=float(bx1)

    """
    # Suchen der Koordinaten aus Lat Lon?
    bxy1=bxy[bxy.rfind('N:'):]
    bxy2=bxy1[:bxy1.rfind('E:')]
    bxy3=bxy2[:bxy2.rfind('S:')]
    bxy4=bxy3[:bxy3.rfind('.')]
    bxy6=bxy4[bxy4.rfind(' '):]
    bxy5=bxy3[bxy3.rfind('.'):]
    by=bxy6,bxy5
    by1="".join(by)
    by_korr=float(by1)
    bxy4=bxy3.rsplit('N:',1)[1]
    bxy5=bxy4[:bxy4.rfind('    ')]
    #bxy6=bxy5.rsplit(' ',2)[1]
    bxy6=bxy5[bxy5.rfind('   '):]
    bxy7=bxy6[bxy6.rfind('   '):]
    bxy1=bxy[bxy.rfind('E:'):]
    bxy2=bxy1[:bxy1.rfind('W:')]
    bxy3=bxy2.rsplit('.',1)[0]
    bxy4=bxy3[bxy3.rfind(' '):]
    bxy5=bxy2.rsplit('.',2)[1]
    bx=bxy4,".",bxy5
    bx1="".join(bx)
    bx_korr=float(bx1)
    
 
    print "Korrigierte X-Koordinate:", bx_korr
    print "Korrigierte Y-Koordinate:", by_korr
    
    region = grass.read_command("g.region", flags="p")
    n1 = region.rsplit("south:",1)[0]
    n2 = n1.rsplit("north:",1)[1]
    n = float(n2)
    s1 = region.rsplit("west:",1)[0]
    s2 = s1.rsplit("south:",1)[1]
    s = float(s2)
    e1 = region.rsplit("nsres:",1)[0]
    e2 = e1.rsplit("east:",1)[1]
    e = float(e2)
    w1 = region.rsplit("east:",1)[0]
    w2 = w1.rsplit("west:",1)[1]
    w = float(w2)
    #print "N:", n
    #print "S:", s
    #print "W:", w
    #print "E:", e
    
    # nur ungefaehre Werte!!
    lat1 = (by_korr + by_korr) / 2 * 0.01745
    dx1 = 111.3 * math.cos(lat1) * (bx_korr - w)
    dy1 = 111.3 * (by_korr - by_korr)
    distance1 = math.sqrt(dx1 * dx1 + dy1 * dy1)
    lat2 = (by_korr + by_korr) / 2 * 0.01745
    dx2 = 111.3 * math.cos(lat2) * (x - e)
    dy2 = 111.3 * (by_korr - by_korr)
    distance2 = math.sqrt(dx2 * dx2 + dy2 * dy2)
    lat3 = (bx_korr + bx_korr) / 2 * 0.01745
    dx3 = 111.3 * math.cos(lat3) * (by_korr - n)
    dy3 = 111.3 * (bx_korr - bx_korr)
    distance3 = math.sqrt(dx3 * dx3 + dy3 * dy3)
    lat4 = (bx_korr + bx_korr) / 2 * 0.01745
    dx4 = 111.3 * math.cos(lat4) * (by_korr - s)
    dy4 = 111.3 * (bx_korr - bx_korr)
    distance4 = math.sqrt(dx4 * dx4 + dy4 * dy4)
    if distance1 < 15:
        kommentar1 = "Westen"
    else:
        kommentar1 = ""
    if distance2 < 15:
        kommentar2 = "Osten"
    else:
        kommentar2= ""
    if distance3 < 15:
        kommentar3 = "Norden"
    else:
        kommentar3= ""
    if distance4 < 15:
        kommentar4 = "Sueden"
    else:
        kommentar4= ""
    """
    Kommentare werden zusammengefasst
    Falls kein Kommentar vorhanden = DGM deckt alles ausreichend ab, dann Kommentar = "DGM OK"
    """
    kommentar5= kommentar1, kommentar2, kommentar3, kommentar4
    dgm_kommentar = "".join(kommentar5)
    if len(dgm_kommentar) < 1:
        dgm_kommentar = "DGM OK"
    else:
        dgm_kommentar1 = "DGM im ", dgm_kommentar, "nicht ausreichend"
        dgm_kommentar = "".join(dgm_kommentar1)
    
    """
    Da die genauen DGM-Daten nun gefunden wurden, werden diese zusammen mit den alten (zur Vergleichbarkeit und Validierung) an eine Tabelle angehaengt,
    die spaeter als *.csv - Datei exportiert wird.
    """
    ergebnis = (name, xg, yg, bx_korr, by_korr, dgm_kommentar)
    ergebnisausgabe.append(ergebnis)
    
    tb = datetime.datetime.now()
    tc = tb - ta
    td = tc * (len(gipfel)-(i+1))
    te = tb+td
    print "---> Restlaufzeit des Moduls:", td
    print "---> Voraussichtliches Ende des Moduls:", te
    
    print ""
    i = i+1

print ergebnisausgabe

"""
Hier wird die Ergebnisliste schliesslich in Tabellenform als *.csv exportiert.
"""
with open('ergebnis_DGM_normal.csv', 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(("Name","X_alt","Y_alt","X_korr", "Y_korr", "DGM-Abdeckung"))
    writer.writerows(ergebnisausgabe)
    
print "Ende des Programms"