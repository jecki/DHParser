const test1* = """
<html>

<head>
<meta http-equiv=Content-Type content="text/html; charset=utf-8">
<meta name=Generator content="Microsoft Word 15 (filtered)">
</heead>
<body>
</body>
</html>
"""

const KSource*: string = """
<html>

<head>
<meta http-equiv=Content-Type content="text/html; charset=utf-8">
<meta name=Generator content="Microsoft Word 15 (filtered)">
<style>
<!--
 /* Font Definitions */
 @font-face
	{font-family:Helvetica;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Courier;
	panose-1:2 7 3 9 2 2 5 2 4 4;}
@font-face
	{font-family:"Tms Rmn";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Helv;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"New York";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:System;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Wingdings;
	panose-1:5 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MS Mincho";
	panose-1:2 2 6 9 4 2 5 8 3 4;}
@font-face
	{font-family:Batang;
	panose-1:2 3 6 0 0 1 1 1 1 1;}
@font-face
	{font-family:SimSun;
	panose-1:2 1 6 0 3 1 1 1 1 1;}
@font-face
	{font-family:PMingLiU;
	panose-1:2 2 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MS Gothic";
	panose-1:2 11 6 9 7 2 5 8 2 4;}
@font-face
	{font-family:Dotum;
	panose-1:2 11 6 0 0 1 1 1 1 1;}
@font-face
	{font-family:SimHei;
	panose-1:2 1 6 9 6 1 1 1 1 1;}
@font-face
	{font-family:MingLiU;
	panose-1:2 2 5 9 0 0 0 0 0 0;}
@font-face
	{font-family:Mincho;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Gulim;
	panose-1:2 11 6 0 0 1 1 1 1 1;}
@font-face
	{font-family:Century;
	panose-1:2 4 6 4 5 5 5 2 3 4;}
@font-face
	{font-family:"Angsana New";
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"Cordia New";
	panose-1:2 11 3 4 2 2 2 2 2 4;}
@font-face
	{font-family:Mangal;
	panose-1:2 4 5 3 5 2 3 3 2 2;}
@font-face
	{font-family:Latha;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Sylfaen;
	panose-1:1 10 5 2 5 3 6 3 3 3;}
@font-face
	{font-family:Vrinda;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:Raavi;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:Shruti;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:Sendnya;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Gautami;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:Tunga;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Estrangelo Edessa";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Cambria Math";
	panose-1:2 4 5 3 5 4 6 3 2 4;}
@font-face
	{font-family:"Yu Gothic";
	panose-1:2 11 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:DengXian;
	panose-1:2 1 6 0 3 1 1 1 1 1;}
@font-face
	{font-family:Calibri;
	panose-1:2 15 5 2 2 2 4 3 2 4;}
@font-face
	{font-family:"Calibri Light";
	panose-1:2 15 3 2 2 2 4 3 2 4;}
@font-face
	{font-family:"Palatino Linotype";
	panose-1:2 4 5 2 5 5 5 3 3 4;}
@font-face
	{font-family:Verdana;
	panose-1:2 11 6 4 3 5 4 4 2 4;}
@font-face
	{font-family:"Arial Unicode MS";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:StplGaramond;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:StplGaramondAkzente;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"StempelGaramond RomanSC";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:NewCenturySchlbk;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:PiEdit-K;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Garamond Antiqua";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Bookman Old Style";
	panose-1:2 5 6 4 5 5 5 2 2 4;}
@font-face
	{font-family:Ahorus;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Tahoma;
	panose-1:2 11 6 4 3 5 4 4 2 4;}
@font-face
	{font-family:Consolas;
	panose-1:2 11 6 9 2 2 4 3 2 4;}
@font-face
	{font-family:OldGreekSerif;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Cambria;
	panose-1:2 4 5 3 5 4 6 3 2 4;}
@font-face
	{font-family:"Stpl Garamond Akzente";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Stpl_ Garamond_ Akzente";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:HumboldtFraktur;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:StempelGaramond;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:StplGaramondAkzente-Italic;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:StplGaramondAkzente-Roman;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"ACADEMY ENGRAVED LET PLAIN\:1\.0";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Al Bayan Plain";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Al Bayan";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Al Tarikh";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"American Typewriter Light";
	panose-1:2 9 3 4 2 0 4 2 3 4;}
@font-face
	{font-family:"American Typewriter Condensed L";
	panose-1:2 9 3 6 2 0 4 2 3 4;}
@font-face
	{font-family:"American Typewriter";
	panose-1:2 9 6 4 2 0 4 2 3 4;}
@font-face
	{font-family:"American Typewriter Condensed";
	panose-1:2 9 6 6 2 0 4 2 3 4;}
@font-face
	{font-family:"AMERICAN TYPEWRITER SEMIBOLD";
	panose-1:2 9 6 4 2 0 4 2 3 4;}
@font-face
	{font-family:"Andale Mono";
	panose-1:2 11 5 9 0 0 0 0 0 4;}
@font-face
	{font-family:"Apple Chancery";
	panose-1:3 2 7 2 4 5 6 6 5 4;}
@font-face
	{font-family:"Apple Braille";
	panose-1:5 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple Braille Outline 6 Dot";
	panose-1:5 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple Braille Outline 8 Dot";
	panose-1:5 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple Braille Pinpoint 6 Dot";
	panose-1:5 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple Braille Pinpoint 8 Dot";
	panose-1:5 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple Color Emoji";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:AppleGothic;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:AppleMyungjo;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple SD Gothic Neo Thin";
	panose-1:2 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple SD Gothic Neo UltraLight";
	panose-1:2 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple SD Gothic Neo Light";
	panose-1:2 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple SD Gothic Neo";
	panose-1:2 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple SD Gothic Neo Medium";
	panose-1:2 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"APPLE SD GOTHIC NEO SEMIBOLD";
	panose-1:2 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"APPLE SD GOTHIC NEO EXTRABOLD";
	panose-1:2 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"APPLE SD GOTHIC NEO HEAVY";
	panose-1:2 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Apple Symbols";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Arial Hebrew Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Arial Hebrew";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Arial Hebrew Scholar Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Arial Hebrew Scholar";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Arial Narrow";
	panose-1:2 11 6 6 2 2 2 3 2 4;}
@font-face
	{font-family:"Avenir Light";
	panose-1:2 11 4 2 2 2 3 2 2 4;}
@font-face
	{font-family:"AVENIR LIGHT OBLIQUE";
	panose-1:2 11 4 2 2 2 3 9 2 4;}
@font-face
	{font-family:"Avenir Book";
	panose-1:2 0 5 3 2 0 0 2 0 3;}
@font-face
	{font-family:Avenir;
	panose-1:2 0 5 3 2 0 0 2 0 3;}
@font-face
	{font-family:"AVENIR BOOK OBLIQUE";
	panose-1:2 0 5 3 2 0 0 2 0 3;}
@font-face
	{font-family:"AVENIR OBLIQUE";
	panose-1:2 11 5 3 2 2 3 9 2 4;}
@font-face
	{font-family:"Avenir Medium";
	panose-1:2 0 6 3 2 0 0 2 0 3;}
@font-face
	{font-family:"AVENIR MEDIUM OBLIQUE";
	panose-1:2 0 6 3 2 0 0 2 0 3;}
@font-face
	{font-family:"Avenir Black";
	panose-1:2 11 8 3 2 2 3 2 2 4;}
@font-face
	{font-family:"Avenir Black Oblique";
	panose-1:2 11 8 3 2 2 3 9 2 4;}
@font-face
	{font-family:"Avenir Heavy";
	panose-1:2 11 7 3 2 2 3 2 2 4;}
@font-face
	{font-family:"AVENIR HEAVY OBLIQUE";
	panose-1:2 11 7 3 2 2 3 9 2 4;}
@font-face
	{font-family:"Avenir Next Ultra Light";
	panose-1:2 11 2 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next";
	panose-1:2 11 5 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next Medium";
	panose-1:2 11 6 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next Demi Bold";
	panose-1:2 11 7 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next Heavy";
	panose-1:2 11 9 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next Condensed Ultra Lig";
	panose-1:2 11 2 6 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next Condensed";
	panose-1:2 11 5 6 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next Condensed Medium";
	panose-1:2 11 6 6 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next Condensed Demi Bold";
	panose-1:2 11 7 6 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next Condensed Heavy";
	panose-1:2 11 9 6 2 2 2 2 2 4;}
@font-face
	{font-family:Ayuthaya;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Baghdad;
	panose-1:1 0 5 0 0 0 0 2 0 4;}
@font-face
	{font-family:"Bangla MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bangla Sangam MN";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Baskerville;
	panose-1:2 2 5 2 7 4 1 2 3 3;}
@font-face
	{font-family:"BASKERVILLE SEMIBOLD";
	panose-1:2 2 7 2 7 4 0 2 2 3;}
@font-face
	{font-family:Beirut;
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Big Caslon Medium";
	panose-1:2 0 6 3 9 0 0 2 0 3;}
@font-face
	{font-family:"Bodoni Ornaments";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bodoni 72 Book";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bodoni 72";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bodoni 72 Oldstyle Book";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bodoni 72 Oldstyle";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bodoni 72 Smallcaps Book";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bradley Hand";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Brush Script MT";
	panose-1:3 6 8 2 4 4 6 7 3 4;}
@font-face
	{font-family:Chalkboard;
	panose-1:3 5 6 2 4 2 2 2 2 5;}
@font-face
	{font-family:"Chalkboard SE Light";
	panose-1:3 5 6 2 4 2 2 2 2 5;}
@font-face
	{font-family:"Chalkboard SE";
	panose-1:3 5 6 2 4 2 2 2 2 5;}
@font-face
	{font-family:Chalkduster;
	panose-1:3 5 6 2 4 2 2 2 2 5;}
@font-face
	{font-family:"Charter Roman";
	panose-1:2 4 5 3 5 5 6 2 2 3;}
@font-face
	{font-family:Charter;
	panose-1:2 4 5 3 5 5 6 2 2 3;}
@font-face
	{font-family:"Charter Black";
	panose-1:2 4 8 3 5 5 6 2 2 3;}
@font-face
	{font-family:Cochin;
	panose-1:2 0 6 3 2 0 0 2 0 3;}
@font-face
	{font-family:"Comic Sans MS";
	panose-1:3 15 7 2 3 3 2 2 2 4;}
@font-face
	{font-family:"Copperplate Light";
	panose-1:2 0 6 4 3 0 0 2 0 4;}
@font-face
	{font-family:Copperplate;
	panose-1:2 0 5 4 0 0 0 2 0 4;}
@font-face
	{font-family:"Corsiva Hebrew";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"DIN Alternate";
	panose-1:2 11 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"DIN Condensed";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"DecoType Naskh";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Devanagari MT";
	panose-1:2 0 5 0 2 0 0 0 0 0;}
@font-face
	{font-family:"Devanagari Sangam MN";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Didot;
	panose-1:2 0 5 3 0 0 0 2 0 3;}
@font-face
	{font-family:"Diwan Kufi";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Mishafi Gold";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Diwan Thuluth";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Euphemia UCAS";
	panose-1:2 11 5 3 4 1 2 2 1 4;}
@font-face
	{font-family:Farisi;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Futura Medium";
	panose-1:2 11 6 2 2 2 4 2 3 3;}
@font-face
	{font-family:"Futura Condensed Medium";
	panose-1:2 11 5 6 2 2 4 3 2 4;}
@font-face
	{font-family:Futura;
	panose-1:2 11 6 2 2 2 4 2 3 3;}
@font-face
	{font-family:"FUTURA CONDENSED EXTRABOLD";
	panose-1:2 11 8 6 2 2 4 3 2 4;}
@font-face
	{font-family:Galvji;
	panose-1:2 11 5 4 2 2 2 2 2 4;}
@font-face
	{font-family:"GALVJI OBLIQUE";
	panose-1:2 11 5 4 2 2 2 2 2 4;}
@font-face
	{font-family:GALVJI-BOLDOBLIQUE;
	panose-1:2 11 5 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Geeza Pro";
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Geneva;
	panose-1:2 11 5 3 3 4 4 4 2 4;}
@font-face
	{font-family:Georgia;
	panose-1:2 4 5 2 5 4 5 2 3 3;}
@font-face
	{font-family:"Gill Sans Light";
	panose-1:2 11 3 2 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans";
	panose-1:2 11 5 2 2 1 4 2 2 3;}
@font-face
	{font-family:"GILL SANS SEMIBOLD";
	panose-1:2 11 7 2 2 1 4 2 2 3;}
@font-face
	{font-family:"Tamil Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Grantha Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Gujarati MT";
	panose-1:0 0 5 0 7 0 0 0 0 0;}
@font-face
	{font-family:"Gujarati Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Gurmukhi MN";
	panose-1:2 2 6 0 5 4 5 2 3 4;}
@font-face
	{font-family:"Gurmukhi Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Helvetica Light";
	panose-1:2 11 4 3 2 2 2 2 2 4;}
@font-face
	{font-family:"HELVETICA LIGHT OBLIQUE";
	panose-1:2 11 4 3 2 2 2 2 2 4;}
@font-face
	{font-family:"HELVETICA OBLIQUE";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"HELVETICA BOLD OBLIQUE";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Helvetica Neue UltraLight";
	panose-1:2 0 2 6 0 0 0 2 0 4;}
@font-face
	{font-family:"Helvetica Neue Thin";
	panose-1:2 11 4 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Helvetica Neue Light";
	panose-1:2 0 4 3 0 0 0 2 0 4;}
@font-face
	{font-family:"Helvetica Neue";
	panose-1:2 0 5 3 0 0 0 2 0 4;}
@font-face
	{font-family:"Helvetica Neue Medium";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"HELVETICA NEUE CONDENSED";
	panose-1:2 0 8 6 0 0 0 2 0 4;}
@font-face
	{font-family:"HELVETICA NEUE CONDENSED BLACK";
	panose-1:2 0 10 6 0 0 0 2 0 4;}
@font-face
	{font-family:Herculanum;
	panose-1:2 0 5 5 0 0 0 2 0 4;}
@font-face
	{font-family:"Hiragino Maru Gothic Pro W4";
	panose-1:2 15 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Maru Gothic ProN W4";
	panose-1:2 15 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Mincho ProN W3";
	panose-1:2 2 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Mincho ProN W6";
	panose-1:2 2 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Mincho Pro W3";
	panose-1:2 2 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Mincho Pro W6";
	panose-1:2 2 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W0";
	panose-1:2 11 2 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W1";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W2";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W3";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W4";
	panose-1:2 11 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W5";
	panose-1:2 11 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W6";
	panose-1:2 11 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W7";
	panose-1:2 11 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W8";
	panose-1:2 11 8 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans W9";
	panose-1:2 11 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Kaku Gothic ProN W3";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Kaku Gothic ProN W6";
	panose-1:2 11 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Kaku Gothic Pro W3";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Kaku Gothic Pro W6";
	panose-1:2 11 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Kaku Gothic Std W8";
	panose-1:2 11 8 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Kaku Gothic StdN W8";
	panose-1:2 11 8 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans GB W3";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hiragino Sans GB W6";
	panose-1:2 11 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hoefler Text";
	panose-1:2 3 6 2 5 5 6 2 2 3;}
@font-face
	{font-family:"Hoefler Text Ornaments";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"HOEFLER TEXT BLACK";
	panose-1:2 3 8 2 6 7 6 2 2 3;}
@font-face
	{font-family:ITFDEVANAGARI-LIGHT;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:ITFDEVANAGARI-BOOK;
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:ITFDEVANAGARI-MEDIUM;
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:ITFDEVANAGARI-DEMI;
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"ITF Devanagari";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"ITFDEVANAGARI MARATHI LIGHT";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"ITFDEVANAGARI MARATHI-BOOK";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"ITF Devanagari Marathi Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"ITFDEVANAGARI MARATHI-DEMI";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"ITF Devanagari Marathi";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Impact;
	panose-1:2 11 8 6 3 9 2 5 2 4;}
@font-face
	{font-family:InaiMathi;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Kailasa;
	panose-1:2 0 5 0 0 0 0 2 0 4;}
@font-face
	{font-family:"Kannada MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kannada Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Kefa;
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:"Khmer MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Khmer Sangam MN";
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Bangla Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Bangla";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Bangla Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"KOHINOOR BANGLA SEMIBOLD";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Devanagari Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Devanagari";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Devanagari Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"KOHINOOR DEVANAGARI SEMIBOLD";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Gujarati Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Gujarati";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Gujarati Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"KOHINOOR GUJARATI SEMIBOLD";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Telugu Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Telugu";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kohinoor Telugu Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"KOHINOOR TELUGU SEMIBOLD";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Kokonor;
	panose-1:1 0 5 0 0 0 0 2 0 3;}
@font-face
	{font-family:Krungthep;
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:KufiStandardGK;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Lao MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Lao Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libertinus Keyboard";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Libertinus Math";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Libertinus Mono";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Libertinus Sans";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Libertinus Serif";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Libertinus Serif Semibold";
	panose-1:2 0 7 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Libertinus Serif Display";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Libertinus Serif Initials";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Linux Biolinum O";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Linux Biolinum Keyboard O";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Linux Libertine Display O";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"LINUX LIBERTINE INITIALS O";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"LINUX LIBERTINE MONO O";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Linux Libertine O";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"LINUX LIBERTINE O SEMIBOLD";
	panose-1:2 0 7 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Lucida Grande";
	panose-1:2 11 6 0 4 5 2 2 2 4;}
@font-face
	{font-family:Luminari;
	panose-1:2 0 5 5 0 0 0 2 0 4;}
@font-face
	{font-family:"Malayalam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Malayalam Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Marker Felt Thin";
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MARKER FELT WIDE";
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Menlo;
	panose-1:2 11 6 9 3 8 4 2 2 4;}
@font-face
	{font-family:"Microsoft Sans Serif";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Monaco;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Gurmukhi MT";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Mshtakan;
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MSHTAKAN OBLIQUE";
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MSHTAKAN BOLDOBLIQUE";
	panose-1:2 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MuktaMahee ExtraLight";
	panose-1:2 11 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MuktaMahee Light";
	panose-1:2 11 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MuktaMahee Regular";
	panose-1:2 11 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MuktaMahee Medium";
	panose-1:2 11 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MuktaMahee SemiBold";
	panose-1:2 11 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MuktaMahee Bold";
	panose-1:2 11 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MuktaMahee ExtraBold";
	panose-1:2 11 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Muna;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MUNA BLACK";
	panose-1:0 0 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:Nadeem;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"New Peninim MT";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"NEW PENINIM MT INCLINED";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"NEW PENINIM MT BOLD INCLINED";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noteworthy Light";
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Noteworthy;
	panose-1:2 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Nastaliq Urdu";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Batak";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kannada Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kannada ExtraLight";
	panose-1:2 11 3 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kannada Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kannada";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kannada Medium";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kannada SemiBold";
	panose-1:2 11 7 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kannada ExtraBold";
	panose-1:2 11 9 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kannada Black";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar ExtLt";
	panose-1:2 11 3 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar Med";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar SemBd";
	panose-1:2 11 7 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar ExtBd";
	panose-1:2 11 9 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar Blk";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zawgyi Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zawgyi ExtLt";
	panose-1:2 11 3 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zawgyi Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zawgyi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zawgyi Med";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zawgyi SemBd";
	panose-1:2 11 7 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zawgyi ExtBd";
	panose-1:2 11 9 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zawgyi Blk";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans NKo";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Oriya";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Tagalog";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Serif Myanmar Thin";
	panose-1:2 2 2 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Myanmar ExtLt";
	panose-1:2 2 3 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Myanmar Light";
	panose-1:2 2 4 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Myanmar";
	panose-1:2 2 5 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Myanmar Med";
	panose-1:2 2 6 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Myanmar SemBd";
	panose-1:2 2 7 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Myanmar ExtBd";
	panose-1:2 2 9 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Myanmar Blk";
	panose-1:2 2 10 2 6 5 5 2 2 4;}
@font-face
	{font-family:Optima;
	panose-1:2 0 5 3 6 0 0 2 0 4;}
@font-face
	{font-family:"OPTIMA EXTRABLACK";
	panose-1:2 0 11 3 0 0 0 2 0 4;}
@font-face
	{font-family:"Oriya MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Oriya Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PT Mono";
	panose-1:2 6 5 9 2 2 5 2 2 4;}
@font-face
	{font-family:"PT Sans";
	panose-1:2 11 5 3 2 2 3 2 2 4;}
@font-face
	{font-family:"PT Sans Narrow";
	panose-1:2 11 5 6 2 2 3 2 2 4;}
@font-face
	{font-family:"PT Sans Caption";
	panose-1:2 11 6 3 2 2 3 2 2 4;}
@font-face
	{font-family:"PT Serif";
	panose-1:2 10 6 3 4 5 5 2 2 4;}
@font-face
	{font-family:"PT Serif Caption";
	panose-1:2 6 6 3 5 5 5 2 2 4;}
@font-face
	{font-family:Palatino;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Papyrus;
	panose-1:2 11 6 2 4 2 0 2 3 3;}
@font-face
	{font-family:"Papyrus Condensed";
	panose-1:2 11 6 2 4 2 0 2 3 3;}
@font-face
	{font-family:"Party LET Plain";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Phosphate Inline";
	panose-1:2 0 5 6 5 0 0 2 0 4;}
@font-face
	{font-family:"Phosphate Solid";
	panose-1:2 0 5 6 5 0 0 2 0 4;}
@font-face
	{font-family:"PingFang HK Ultralight";
	panose-1:2 11 1 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang HK Thin";
	panose-1:2 11 2 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang HK Light";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang HK";
	panose-1:2 11 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang HK Medium";
	panose-1:2 11 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PINGFANG HK SEMIBOLD";
	panose-1:2 11 8 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang TC Ultralight";
	panose-1:2 11 1 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang TC Thin";
	panose-1:2 11 2 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang TC Light";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang TC";
	panose-1:2 11 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang TC Medium";
	panose-1:2 11 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PINGFANG TC SEMIBOLD";
	panose-1:2 11 8 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang SC Ultralight";
	panose-1:2 11 1 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang SC Thin";
	panose-1:2 11 2 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang SC Light";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang SC";
	panose-1:2 11 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PingFang SC Medium";
	panose-1:2 11 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"PINGFANG SC SEMIBOLD";
	panose-1:2 11 8 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Plantagenet Cherokee";
	panose-1:2 2 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Raanana;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Heiti TC Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Heiti TC Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Heiti SC Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Heiti SC Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"STIX Two Math";
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"STIX Two Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"STIX Two Text Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"STIX Two Text SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Songti SC Light";
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:"Songti SC";
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:"SONGTI SC BLACK";
	panose-1:2 1 8 0 4 1 1 1 1 1;}
@font-face
	{font-family:"Songti TC Light";
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:"Songti TC";
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:STSong;
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:Sana;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Sathu;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"SAVOYE LET PLAIN\:1\.0";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Shree Devanagari 714";
	panose-1:2 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:SignPainter-HouseScript;
	panose-1:2 0 0 6 7 0 0 2 0 4;}
@font-face
	{font-family:"SIGNPAINTER-HOUSESCRIPT SEMIBOL";
	panose-1:2 0 0 6 7 0 0 2 0 4;}
@font-face
	{font-family:Silom;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sinhala MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sinhala Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Skia;
	panose-1:2 13 5 2 2 2 4 2 2 4;}
@font-face
	{font-family:"Snell Roundhand";
	panose-1:2 0 6 3 8 0 0 9 0 4;}
@font-face
	{font-family:"SNELL ROUNDHAND BLACK";
	panose-1:2 0 10 4 9 0 0 9 0 4;}
@font-face
	{font-family:SUKHUMVITSET-THIN;
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:SUKHUMVITSET-LIGHT;
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:SUKHUMVITSET-TEXT;
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:SUKHUMVITSET-MEDIUM;
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:SUKHUMVITSET-SEMIBOLD;
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:"Sukhumvit Set";
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:"Tamil MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Telugu MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Telugu Sangam MN";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Trattatello;
	panose-1:2 15 4 3 2 2 0 2 3 3;}
@font-face
	{font-family:"Trebuchet MS";
	panose-1:2 11 6 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Waseem Light";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:Waseem;
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Zapfino;
	panose-1:3 3 3 0 4 7 7 7 12 3;}
@font-face
	{font-family:"Abadi MT Condensed Light";
	panose-1:2 11 3 6 3 1 1 1 1 3;}
@font-face
	{font-family:"Abadi MT Condensed Extra Bold";
	panose-1:2 11 10 6 3 1 1 1 1 3;}
@font-face
	{font-family:"Aptos Light";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:Aptos;
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Aptos SemiBold";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Aptos ExtraBold";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Aptos Black";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Aptos Narrow";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Arial Black";
	panose-1:2 11 10 4 2 1 2 2 2 4;}
@font-face
	{font-family:"Arial Rounded MT Bold";
	panose-1:2 15 7 4 3 5 4 3 2 4;}
@font-face
	{font-family:"Baskerville Old Face";
	panose-1:2 2 6 2 8 5 5 2 3 3;}
@font-face
	{font-family:BatangChe;
	panose-1:2 3 6 9 0 1 1 1 1 1;}
@font-face
	{font-family:Gungsuh;
	panose-1:2 3 6 0 0 1 1 1 1 1;}
@font-face
	{font-family:GungsuhChe;
	panose-1:2 3 6 9 0 1 1 1 1 1;}
@font-face
	{font-family:"Bauhaus 93";
	panose-1:4 3 9 5 2 11 2 2 12 2;}
@font-face
	{font-family:"Bell MT";
	panose-1:2 2 5 3 6 3 5 2 3 3;}
@font-face
	{font-family:"Bernard MT Condensed";
	panose-1:2 5 8 6 6 9 5 2 4 4;}
@font-face
	{font-family:"Book Antiqua";
	panose-1:2 4 6 2 5 3 5 3 3 4;}
@font-face
	{font-family:"Bookshelf Symbol 7";
	panose-1:5 1 1 1 1 1 1 1 1 1;}
@font-face
	{font-family:Braggadocio;
	panose-1:4 3 11 7 13 11 2 2 4 3;}
@font-face
	{font-family:"Britannic Bold";
	panose-1:2 11 9 3 6 7 3 2 2 4;}
@font-face
	{font-family:"Calisto MT";
	panose-1:2 4 6 3 5 5 5 3 3 4;}
@font-face
	{font-family:Candara;
	panose-1:2 14 5 2 3 3 3 2 2 4;}
@font-face
	{font-family:"Century Gothic";
	panose-1:2 11 5 2 2 2 2 2 2 4;}
@font-face
	{font-family:"Century Schoolbook";
	panose-1:2 4 6 4 5 5 5 2 3 4;}
@font-face
	{font-family:"Colonna MT";
	panose-1:4 2 8 5 6 2 2 3 2 3;}
@font-face
	{font-family:Constantia;
	panose-1:2 3 6 2 5 3 6 3 3 3;}
@font-face
	{font-family:"Cooper Black";
	panose-1:2 8 9 4 4 3 11 2 4 4;}
@font-face
	{font-family:"Copperplate Gothic Bold";
	panose-1:2 14 7 5 2 2 6 2 4 4;}
@font-face
	{font-family:Corbel;
	panose-1:2 11 5 3 2 2 4 2 2 4;}
@font-face
	{font-family:CordiaUPC;
	panose-1:2 11 3 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Curlz MT";
	panose-1:4 4 4 4 5 7 2 2 2 2;}
@font-face
	{font-family:David;
	panose-1:2 14 5 2 6 4 1 1 1 1;}
@font-face
	{font-family:"DengXian Light";
	panose-1:2 1 6 0 3 1 1 1 1 1;}
@font-face
	{font-family:Desdemona;
	panose-1:4 2 5 5 2 14 3 4 5 4;}
@font-face
	{font-family:"Dubai Light";
	panose-1:2 11 3 3 3 4 3 3 2 4;}
@font-face
	{font-family:Dubai;
	panose-1:2 11 5 3 3 4 3 3 2 4;}
@font-face
	{font-family:"Dubai Medium";
	panose-1:2 11 6 3 3 4 3 3 2 4;}
@font-face
	{font-family:"Edwardian Script ITC";
	panose-1:3 3 3 2 4 7 7 13 8 4;}
@font-face
	{font-family:"Engravers MT";
	panose-1:2 9 7 7 8 5 5 2 3 4;}
@font-face
	{font-family:Eurostile;
	panose-1:2 11 5 4 2 2 2 5 2 4;}
@font-face
	{font-family:FangSong;
	panose-1:2 1 6 9 6 1 1 1 1 1;}
@font-face
	{font-family:"Footlight MT Light";
	panose-1:2 4 6 2 6 3 10 2 3 4;}
@font-face
	{font-family:"Franklin Gothic Book";
	panose-1:2 11 5 3 2 1 2 2 2 4;}
@font-face
	{font-family:"Franklin Gothic Medium";
	panose-1:2 11 6 3 2 1 2 2 2 4;}
@font-face
	{font-family:"Franklin Gothic Medium Cond";
	panose-1:2 11 6 6 3 4 2 2 2 4;}
@font-face
	{font-family:"Franklin Gothic Demi";
	panose-1:2 11 7 3 2 1 2 2 2 4;}
@font-face
	{font-family:"Franklin Gothic Demi Cond";
	panose-1:2 11 7 6 3 4 2 2 2 4;}
@font-face
	{font-family:"Franklin Gothic Heavy";
	panose-1:2 11 9 3 2 1 2 2 2 4;}
@font-face
	{font-family:Gabriola;
	panose-1:4 4 6 5 5 16 2 2 13 2;}
@font-face
	{font-family:Garamond;
	panose-1:2 2 4 4 3 3 1 1 8 3;}
@font-face
	{font-family:"Gill Sans MT";
	panose-1:2 11 5 2 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans MT Condensed";
	panose-1:2 11 5 6 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans MT Ext Condensed Bold";
	panose-1:2 11 9 2 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans Ultra Bold";
	panose-1:2 11 10 2 2 1 4 2 2 3;}
@font-face
	{font-family:"Gloucester MT Extra Condensed";
	panose-1:2 3 8 8 2 6 1 1 1 1;}
@font-face
	{font-family:"Goudy Old Style";
	panose-1:2 2 5 2 5 3 5 2 3 3;}
@font-face
	{font-family:GulimChe;
	panose-1:2 11 6 9 0 1 1 1 1 1;}
@font-face
	{font-family:DotumChe;
	panose-1:2 11 6 9 0 1 1 1 1 1;}
@font-face
	{font-family:Haettenschweiler;
	panose-1:2 11 7 6 4 9 2 6 2 4;}
@font-face
	{font-family:Harrington;
	panose-1:4 4 5 5 5 10 2 2 7 2;}
@font-face
	{font-family:HGGothicE;
	panose-1:2 11 9 9 0 0 0 0 0 0;}
@font-face
	{font-family:HGPGothicE;
	panose-1:2 11 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:HGSGothicE;
	panose-1:2 11 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:HGMinchoE;
	panose-1:2 2 9 9 0 0 0 0 0 0;}
@font-face
	{font-family:HGPMinchoE;
	panose-1:2 2 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:HGSMinchoE;
	panose-1:2 2 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:HGSoeiKakugothicUB;
	panose-1:2 11 9 9 0 0 0 0 0 0;}
@font-face
	{font-family:HGPSoeiKakugothicUB;
	panose-1:2 11 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:HGSSoeiKakugothicUB;
	panose-1:2 11 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:HGMaruGothicMPRO;
	panose-1:2 15 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Microsoft Himalaya";
	panose-1:1 1 1 0 1 1 1 1 1 1;}
@font-face
	{font-family:"Imprint MT Shadow";
	panose-1:4 2 6 5 6 3 3 3 2 2;}
@font-face
	{font-family:KaiTi;
	panose-1:2 1 6 9 6 1 1 1 1 1;}
@font-face
	{font-family:Kartika;
	panose-1:2 2 5 3 3 4 4 6 2 3;}
@font-face
	{font-family:"Kino MT";
	panose-1:4 3 7 5 13 12 2 2 7 3;}
@font-face
	{font-family:"Lucida Console";
	panose-1:2 11 6 9 4 5 4 2 2 4;}
@font-face
	{font-family:"Lucida Sans";
	panose-1:2 11 6 2 3 5 4 2 2 4;}
@font-face
	{font-family:"Lucida Sans Unicode";
	panose-1:2 11 6 2 3 5 4 2 2 4;}
@font-face
	{font-family:"Lucida Blackletter";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Lucida Bright";
	panose-1:2 4 6 2 5 5 5 2 3 4;}
@font-face
	{font-family:"Lucida Calligraphy";
	panose-1:3 1 1 1 1 1 1 1 1 1;}
@font-face
	{font-family:"Lucida Fax";
	panose-1:2 6 6 2 5 5 5 2 2 4;}
@font-face
	{font-family:"Lucida Handwriting";
	panose-1:3 1 1 1 1 1 1 1 1 1;}
@font-face
	{font-family:"Lucida Sans Typewriter";
	panose-1:2 11 5 9 3 5 4 3 2 4;}
@font-face
	{font-family:"Malgun Gothic Semilight";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Malgun Gothic";
	panose-1:2 11 5 3 2 0 0 2 0 4;}
@font-face
	{font-family:Marlett;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Matura MT Script Capitals";
	panose-1:3 2 8 2 6 6 2 7 2 2;}
@font-face
	{font-family:Meiryo;
	panose-1:2 11 6 4 3 5 4 4 2 4;}
@font-face
	{font-family:"Meiryo UI";
	panose-1:2 11 6 4 3 5 4 4 2 4;}
@font-face
	{font-family:MingLiU_HKSCS;
	panose-1:2 2 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:MingLiU-ExtB;
	panose-1:2 2 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:PMingLiU-ExtB;
	panose-1:2 2 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:MingLiU_HKSCS-ExtB;
	panose-1:2 2 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Mistral;
	panose-1:3 9 7 2 3 4 7 2 4 3;}
@font-face
	{font-family:"Myanmar Text";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Modern No\. 20";
	panose-1:2 7 7 4 7 5 5 2 3 3;}
@font-face
	{font-family:"Mongolian Baiti";
	panose-1:3 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Monotype Corsiva";
	panose-1:3 1 1 1 1 2 1 1 1 1;}
@font-face
	{font-family:"Monotype Sorts";
	panose-1:1 1 6 1 1 1 1 1 1 1;}
@font-face
	{font-family:"MS Reference Sans Serif";
	panose-1:2 11 6 4 3 5 4 4 2 4;}
@font-face
	{font-family:"MS Reference Specialty";
	panose-1:5 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MS UI Gothic";
	panose-1:2 11 6 0 7 2 5 8 2 4;}
@font-face
	{font-family:"MS PGothic";
	panose-1:2 11 6 0 7 2 5 8 2 4;}
@font-face
	{font-family:"Microsoft JhengHei";
	panose-1:2 11 6 4 3 5 4 4 2 4;}
@font-face
	{font-family:"MS PMincho";
	panose-1:2 2 6 0 4 2 5 8 3 4;}
@font-face
	{font-family:"Microsoft YaHei Light";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Microsoft YaHei";
	panose-1:2 11 5 3 2 2 4 2 2 4;}
@font-face
	{font-family:"Microsoft YaHei UI Light";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Microsoft YaHei UI";
	panose-1:2 11 5 3 2 2 4 2 2 4;}
@font-face
	{font-family:"Microsoft Yi Baiti";
	panose-1:3 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MT Extra";
	panose-1:5 5 1 2 1 2 5 2 2 2;}
@font-face
	{font-family:"News Gothic MT";
	panose-1:2 11 5 3 2 1 3 2 2 3;}
@font-face
	{font-family:"Microsoft New Tai Lue";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:Nyala;
	panose-1:2 0 5 4 7 3 0 2 0 3;}
@font-face
	{font-family:Onyx;
	panose-1:4 5 6 2 8 7 2 2 2 3;}
@font-face
	{font-family:Perpetua;
	panose-1:2 2 5 2 6 4 1 2 3 3;}
@font-face
	{font-family:"Perpetua Titling MT";
	panose-1:2 2 5 2 6 5 5 2 8 4;}
@font-face
	{font-family:Rockwell;
	panose-1:2 6 6 3 2 2 5 2 4 3;}
@font-face
	{font-family:"Rockwell Condensed";
	panose-1:2 6 6 3 5 4 5 2 1 4;}
@font-face
	{font-family:"Rockwell Extra Bold";
	panose-1:2 6 9 3 4 5 5 2 4 3;}
@font-face
	{font-family:"Segoe Print";
	panose-1:2 0 8 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Script";
	panose-1:3 11 8 4 2 0 0 0 0 3;}
@font-face
	{font-family:"Segoe UI Historic";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe UI Symbol";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:NSimSun;
	panose-1:2 1 6 9 3 1 1 1 1 1;}
@font-face
	{font-family:SimSun-ExtB;
	panose-1:2 1 6 9 6 1 1 1 1 1;}
@font-face
	{font-family:Stencil;
	panose-1:4 4 9 5 13 8 2 2 4 4;}
@font-face
	{font-family:STHupo;
	panose-1:2 1 8 0 4 1 1 1 1 1;}
@font-face
	{font-family:STLiti;
	panose-1:2 1 8 0 4 1 1 1 1 1;}
@font-face
	{font-family:STXingkai;
	panose-1:2 1 8 0 4 1 1 1 1 1;}
@font-face
	{font-family:STXinwei;
	panose-1:2 1 8 0 4 1 1 1 1 1;}
@font-face
	{font-family:STZhongsong;
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:"Microsoft Tai Le";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"TH SarabunPSK";
	panose-1:2 11 5 0 4 2 0 2 0 3;}
@font-face
	{font-family:"Tw Cen MT";
	panose-1:2 11 6 2 2 1 4 2 6 3;}
@font-face
	{font-family:"Tw Cen MT Condensed";
	panose-1:2 11 6 6 2 1 4 2 2 3;}
@font-face
	{font-family:"Tw Cen MT Condensed Extra Bold";
	panose-1:2 11 8 3 2 2 2 2 2 4;}
@font-face
	{font-family:Webdings;
	panose-1:5 3 1 2 1 5 9 6 7 3;}
@font-face
	{font-family:"Wide Latin";
	panose-1:2 10 10 7 5 5 5 2 4 4;}
@font-face
	{font-family:"Wingdings 2";
	panose-1:5 2 1 2 1 5 7 7 7 7;}
@font-face
	{font-family:"Wingdings 3";
	panose-1:5 4 1 2 1 8 7 7 7 7;}
@font-face
	{font-family:"Yu Gothic Light";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Yu Gothic Medium";
	panose-1:2 11 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Yu Gothic UI Light";
	panose-1:2 11 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Yu Gothic UI Semilight";
	panose-1:2 11 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Yu Gothic UI";
	panose-1:2 11 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Yu Gothic UI Semibold";
	panose-1:2 11 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Yu Mincho Light";
	panose-1:2 2 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Yu Mincho";
	panose-1:2 2 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Yu Mincho Demibold";
	panose-1:2 2 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Abadi Extra Light";
	panose-1:2 11 2 4 2 1 4 2 2 4;}
@font-face
	{font-family:Abadi;
	panose-1:2 11 6 4 2 1 4 2 2 4;}
@font-face
	{font-family:Abel;
	panose-1:2 0 5 6 3 0 0 2 0 4;}
@font-face
	{font-family:"Abril Fatface";
	panose-1:2 0 5 3 0 0 0 2 0 3;}
@font-face
	{font-family:"ADLaM Display";
	panose-1:2 1 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Agency FB";
	panose-1:2 11 5 3 2 2 2 2 2 4;}
@font-face
	{font-family:Aharoni;
	panose-1:2 1 8 3 2 1 4 3 2 3;}
@font-face
	{font-family:"Al Fresco";
	panose-1:2 0 5 7 7 0 0 2 0 2;}
@font-face
	{font-family:"Alasassy Caps";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Aldhabi;
	panose-1:1 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Alef;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Aleo Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Aleo;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Algerian;
	panose-1:4 2 7 5 4 10 2 6 7 2;}
@font-face
	{font-family:"Amasis MT Pro Light";
	panose-1:2 4 3 4 5 0 5 2 3 4;}
@font-face
	{font-family:"Amasis MT Pro";
	panose-1:2 4 5 4 5 0 5 2 3 4;}
@font-face
	{font-family:"Amasis MT Pro Medium";
	panose-1:2 4 6 4 5 0 5 2 3 4;}
@font-face
	{font-family:"Amasis MT Pro Black";
	panose-1:2 4 10 4 5 0 5 2 3 4;}
@font-face
	{font-family:"Amatic SC";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:AngsanaUPC;
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:Anton;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Aparajita;
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"Aptos Display";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Aptos Mono";
	panose-1:2 11 0 9 2 2 2 2 2 4;}
@font-face
	{font-family:"Aptos Serif";
	panose-1:2 2 6 4 7 4 5 2 3 4;}
@font-face
	{font-family:"Arabic Typesetting";
	panose-1:3 2 4 2 4 4 6 3 2 3;}
@font-face
	{font-family:"Aref Ruqaa";
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Arial Nova Cond Light";
	panose-1:2 11 3 6 2 2 2 2 2 4;}
@font-face
	{font-family:"Arial Nova Light";
	panose-1:2 11 3 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Arial Nova Cond";
	panose-1:2 11 5 6 2 2 2 2 2 4;}
@font-face
	{font-family:"Arial Nova";
	panose-1:2 11 5 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Assistant ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Assistant Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Assistant;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Assistant SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Assistant ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Athiti ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Athiti Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Athiti;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Athiti Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Athiti SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Avenir Next LT Pro Light";
	panose-1:2 11 3 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next LT Pro";
	panose-1:2 11 5 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Avenir Next LT Pro Demi";
	panose-1:2 11 7 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Baguet Script";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bahnschrift Light Condensed";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Bahnschrift Light SemiCondensed";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Bahnschrift Light";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Bahnschrift SemiLight Condensed";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Bahnschrift SemiLight";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Bahnschrift Condensed";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Bahnschrift SemiCondensed";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:Bahnschrift;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Bahnschrift SemiBold Condensed";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Bahnschrift SemiBold";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Barlow Condensed Thin";
	panose-1:0 0 3 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Semi Condensed Thin";
	panose-1:0 0 3 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Thin";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Condensed ExtraLight";
	panose-1:0 0 3 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Semi Condensed ExLight";
	panose-1:0 0 3 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Condensed Light";
	panose-1:0 0 4 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Semi Condensed Light";
	panose-1:0 0 4 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Condensed";
	panose-1:0 0 5 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Semi Condensed";
	panose-1:0 0 5 6 0 0 0 0 0 0;}
@font-face
	{font-family:Barlow;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Condensed Medium";
	panose-1:0 0 6 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Semi Condensed Medium";
	panose-1:0 0 6 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Condensed SemiBold";
	panose-1:0 0 7 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Semi Condensed SemiBold";
	panose-1:0 0 7 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Condensed ExtraBold";
	panose-1:0 0 9 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Semi Condensed ExtraBold";
	panose-1:0 0 9 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow ExtraBold";
	panose-1:0 0 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Condensed Black";
	panose-1:0 0 10 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Semi Condensed Black";
	panose-1:0 0 10 6 0 0 0 0 0 0;}
@font-face
	{font-family:"Barlow Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Bebas Neue";
	panose-1:2 11 6 6 2 2 2 5 2 1;}
@font-face
	{font-family:Bembo;
	panose-1:2 2 5 2 5 2 1 2 2 3;}
@font-face
	{font-family:"Berlin Sans FB";
	panose-1:2 14 6 2 2 5 2 2 3 6;}
@font-face
	{font-family:"Berlin Sans FB Demi";
	panose-1:2 14 8 2 2 5 2 2 3 6;}
@font-face
	{font-family:Bierstadt;
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Bierstadt Display";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:BierstadtAlt;
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"BierstadtAlt2 Cond";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"BierstadtAlt3 Cond";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:"BierstadtAlt4 Cond";
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:BierstadtAlt5;
	panose-1:2 11 0 4 2 2 2 2 2 4;}
@font-face
	{font-family:Cond;
	panose-1:2 11 0 4 2 2 2 9 2 4;}
@font-face
	{font-family:"Biome Light";
	panose-1:2 11 3 3 3 2 4 2 8 4;}
@font-face
	{font-family:Biome;
	panose-1:2 11 5 3 3 2 4 2 8 4;}
@font-face
	{font-family:"Blackadder ITC";
	panose-1:4 2 5 5 5 0 7 2 13 2;}
@font-face
	{font-family:"Bodoni MT Condensed";
	panose-1:2 7 6 6 8 6 6 2 2 3;}
@font-face
	{font-family:"Bodoni MT";
	panose-1:2 7 6 3 8 6 6 2 2 3;}
@font-face
	{font-family:"Bodoni MT Black";
	panose-1:2 7 10 3 8 6 6 2 2 3;}
@font-face
	{font-family:"Bodoni MT Poster Compressed";
	panose-1:2 7 7 6 8 6 1 5 2 4;}
@font-face
	{font-family:"Boucherie Block";
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:"Boucherie Sans";
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:"Bradley Hand ITC";
	panose-1:3 7 4 2 5 3 2 3 2 3;}
@font-face
	{font-family:Broadway;
	panose-1:4 4 9 5 8 0 2 2 5 2;}
@font-face
	{font-family:"Browallia New";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:BrowalliaUPC;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Buxton Sketch";
	panose-1:3 8 5 0 0 5 0 0 0 4;}
@font-face
	{font-family:"Californian FB";
	panose-1:2 7 4 3 6 8 11 3 2 4;}
@font-face
	{font-family:Castellar;
	panose-1:2 10 4 2 6 4 6 1 3 1;}
@font-face
	{font-family:"Caveat Brush";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Cavolini;
	panose-1:3 0 5 2 4 3 2 2 2 4;}
@font-face
	{font-family:Centaur;
	panose-1:2 3 5 4 5 2 5 2 3 4;}
@font-face
	{font-family:"Chamberi Super Display";
	panose-1:2 4 5 3 8 5 5 2 3 3;}
@font-face
	{font-family:Charmonman;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Chilgok Gwon Anja";
	panose-1:2 2 6 3 2 1 1 2 1 1;}
@font-face
	{font-family:"Chilgok Kim Yeongbun";
	panose-1:2 2 6 3 2 1 1 2 1 1;}
@font-face
	{font-family:"Chilgok Lee Jonghui";
	panose-1:2 2 6 3 2 1 1 2 1 1;}
@font-face
	{font-family:"Chilgok Lee Wonsun";
	panose-1:2 2 6 3 2 1 1 2 1 1;}
@font-face
	{font-family:Chiller;
	panose-1:4 2 4 4 3 16 7 2 6 2;}
@font-face
	{font-family:Chonburi;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Cochocib Script Latin Pro";
	panose-1:2 0 5 3 0 0 0 2 0 3;}
@font-face
	{font-family:"Concert One";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Congenial UltraLight";
	panose-1:2 0 5 3 4 0 0 2 0 4;}
@font-face
	{font-family:"Congenial Light";
	panose-1:2 0 5 3 4 0 0 2 0 4;}
@font-face
	{font-family:Congenial;
	panose-1:2 0 5 3 4 0 0 2 0 4;}
@font-face
	{font-family:"Congenial SemiBold";
	panose-1:2 0 5 3 4 0 0 2 0 4;}
@font-face
	{font-family:"Congenial Black";
	panose-1:2 0 5 3 4 0 0 2 0 4;}
@font-face
	{font-family:"Convection Condensed";
	panose-1:2 11 6 4 4 5 1 4 2 3;}
@font-face
	{font-family:Convection;
	panose-1:2 11 6 4 4 5 1 4 2 3;}
@font-face
	{font-family:"Convection Extra Bold";
	panose-1:2 11 9 4 4 5 1 4 2 3;}
@font-face
	{font-family:"Convection Symbol";
	panose-1:5 1 1 1 1 1 1 1 1 1;}
@font-face
	{font-family:"Convection UI";
	panose-1:2 11 6 4 4 5 1 4 2 3;}
@font-face
	{font-family:Dante;
	panose-1:2 2 5 2 5 2 0 2 2 3;}
@font-face
	{font-family:DaunPenh;
	panose-1:1 1 1 1 1 1 1 1 1 1;}
@font-face
	{font-family:"Daytona Condensed Light";
	panose-1:2 11 3 6 3 5 3 4 2 4;}
@font-face
	{font-family:"Daytona Light";
	panose-1:2 11 3 4 3 5 3 4 2 4;}
@font-face
	{font-family:"Daytona Condensed";
	panose-1:2 11 5 6 3 5 3 4 2 4;}
@font-face
	{font-family:Daytona;
	panose-1:2 11 6 4 3 5 0 4 2 4;}
@font-face
	{font-family:"Didact Gothic";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:DilleniaUPC;
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"DM Mono Light";
	panose-1:2 11 3 9 4 2 1 4 1 3;}
@font-face
	{font-family:"DM Mono";
	panose-1:2 11 5 9 4 2 1 4 1 3;}
@font-face
	{font-family:"DM Mono Medium";
	panose-1:2 11 6 9 4 2 1 4 1 3;}
@font-face
	{font-family:"DM Sans";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"DM Sans Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"DM Serif Display";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"DM Serif Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:DokChampa;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Dosis ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Dosis Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Dosis;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Dosis Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Dosis SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Dosis ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Dreaming Outloud Pro";
	panose-1:3 5 5 2 4 3 2 3 5 4;}
@font-face
	{font-family:"Dreaming Outloud Script Pro";
	panose-1:3 5 5 2 4 3 4 5 7 4;}
@font-face
	{font-family:"EB Garamond";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"EB Garamond Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"EB Garamond SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"EB Garamond ExtraBold";
	panose-1:0 0 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:Ebrima;
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Elephant;
	panose-1:2 2 9 4 9 5 5 2 3 3;}
@font-face
	{font-family:"Elephant Pro";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Eras Light ITC";
	panose-1:2 11 4 2 3 5 4 2 8 4;}
@font-face
	{font-family:"Eras Medium ITC";
	panose-1:2 11 6 2 3 5 4 2 8 4;}
@font-face
	{font-family:"Eras Demi ITC";
	panose-1:2 11 8 5 3 5 4 2 8 4;}
@font-face
	{font-family:"Eras Bold ITC";
	panose-1:2 11 9 7 3 5 4 2 2 4;}
@font-face
	{font-family:EucrosiaUPC;
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:Euphemia;
	panose-1:2 11 5 3 4 1 2 2 1 4;}
@font-face
	{font-family:"Fahkwang ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Fahkwang Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Fahkwang;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Fahkwang Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Fahkwang SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Fairwater Script Light";
	panose-1:2 0 5 7 0 0 0 2 0 3;}
@font-face
	{font-family:"Fairwater Script";
	panose-1:2 0 5 7 0 0 0 2 0 3;}
@font-face
	{font-family:"Fave Script Bold Pro";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Felix Titling";
	panose-1:4 6 5 5 6 2 2 2 10 4;}
@font-face
	{font-family:"Fira Code Light";
	panose-1:2 11 8 9 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Code";
	panose-1:2 11 8 9 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Code Medium";
	panose-1:2 11 8 9 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Code Retina";
	panose-1:2 11 8 9 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Mono";
	panose-1:2 11 5 9 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Mono Medium";
	panose-1:2 11 6 9 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Extra Condensed Thin";
	panose-1:2 11 3 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Condensed Thin";
	panose-1:2 11 3 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Thin";
	panose-1:2 11 3 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Condensed ExtraLight";
	panose-1:2 11 4 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans ExtraLight";
	panose-1:2 11 4 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Extra Condensed Light";
	panose-1:2 11 4 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Condensed Light";
	panose-1:2 11 4 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Light";
	panose-1:2 11 4 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Extra Condensed";
	panose-1:2 11 5 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Condensed";
	panose-1:2 11 5 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans";
	panose-1:2 11 5 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Condensed Medium";
	panose-1:2 11 6 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Medium";
	panose-1:2 11 6 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Condensed SemiBold";
	panose-1:2 11 6 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans SemiBold";
	panose-1:2 11 6 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Condensed ExtraBold";
	panose-1:2 11 9 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans ExtraBold";
	panose-1:2 11 9 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Extra Condensed Black";
	panose-1:2 11 10 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Condensed Black";
	panose-1:2 11 10 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fira Sans Black";
	panose-1:2 11 10 3 5 0 0 2 0 4;}
@font-face
	{font-family:"Fjalla One";
	panose-1:2 0 5 6 4 0 0 2 0 4;}
@font-face
	{font-family:Forte;
	panose-1:3 6 9 2 4 5 2 7 2 3;}
@font-face
	{font-family:"Forte Forward";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Frank Ruhl Libre Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Frank Ruhl Libre";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Frank Ruhl Libre Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Frank Ruhl Libre Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:FrankRuehl;
	panose-1:2 14 5 3 6 1 1 1 1 1;}
@font-face
	{font-family:"Fredoka One";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:FreesiaUPC;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Freestyle Script";
	panose-1:3 8 4 2 3 2 5 11 4 4;}
@font-face
	{font-family:"French Script MT";
	panose-1:3 2 4 2 4 6 7 4 6 5;}
@font-face
	{font-family:Gabriela;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Gadugi;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Gaegu Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Gaegu;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Georgia Pro Cond Light";
	panose-1:2 4 3 6 5 4 5 2 3 3;}
@font-face
	{font-family:"Georgia Pro Light";
	panose-1:2 4 3 2 5 4 5 2 3 3;}
@font-face
	{font-family:"Georgia Pro Cond";
	panose-1:2 4 5 6 5 4 5 2 3 3;}
@font-face
	{font-family:"Georgia Pro";
	panose-1:2 4 5 2 5 4 5 2 3 3;}
@font-face
	{font-family:"Georgia Pro Cond Semibold";
	panose-1:2 4 7 6 5 4 5 2 3 3;}
@font-face
	{font-family:"Georgia Pro Semibold";
	panose-1:2 4 7 2 5 4 5 2 3 3;}
@font-face
	{font-family:"Georgia Pro Cond Black";
	panose-1:2 4 10 6 5 4 5 2 2 3;}
@font-face
	{font-family:"Georgia Pro Black";
	panose-1:2 4 10 2 5 4 5 2 2 3;}
@font-face
	{font-family:Gigi;
	panose-1:4 4 5 4 6 0 7 2 13 2;}
@font-face
	{font-family:"Gill Sans Nova Cond Lt";
	panose-1:2 11 3 6 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans Nova Light";
	panose-1:2 11 3 2 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans Nova Cond";
	panose-1:2 11 6 6 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans Nova";
	panose-1:2 11 6 2 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans Nova Cond XBd";
	panose-1:2 11 10 6 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans Nova Cond Ultra Bold";
	panose-1:2 11 11 4 2 1 4 2 2 3;}
@font-face
	{font-family:"Gill Sans Nova Ultra Bold";
	panose-1:2 11 11 2 2 1 4 2 2 3;}
@font-face
	{font-family:Gisha;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Goudy Stout";
	panose-1:2 2 9 4 7 3 11 2 4 1;}
@font-face
	{font-family:"Goudy Type";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Grandview;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Grandview Display";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Grotesque Light";
	panose-1:2 11 3 4 2 2 2 2 2 4;}
@font-face
	{font-family:Grotesque;
	panose-1:2 11 5 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Hadassah Friedlaender";
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"Hammersmith One";
	panose-1:2 1 7 3 3 5 1 6 5 4;}
@font-face
	{font-family:"Heebo Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Heebo Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Heebo;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Heebo Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Heebo ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Heebo Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"High Tower Text";
	panose-1:2 4 5 2 5 5 6 3 3 3;}
@font-face
	{font-family:"Hind Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Hind;
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Colombo Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Colombo";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Colombo Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Colombo SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Guntur Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Guntur";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Guntur Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Guntur SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Jalandhar Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Jalandhar";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Jalandhar Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Jalandhar SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Kochi Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Kochi";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Kochi Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Kochi SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Madurai Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Madurai";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Madurai Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Madurai SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Mysuru Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Mysuru";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Mysuru Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Mysuru SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Siliguri Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Siliguri";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Siliguri Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Siliguri SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Vadodara Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Vadodara";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Vadodara Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Hind Vadodara SemiBold";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"IBM Plex Mono Thin";
	panose-1:2 11 3 9 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Mono ExtraLight";
	panose-1:2 11 3 9 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Mono Light";
	panose-1:2 11 4 9 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Mono";
	panose-1:2 11 5 9 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Mono Medium";
	panose-1:2 11 6 9 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Mono SemiBold";
	panose-1:2 11 7 9 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans Condensed Thin";
	panose-1:2 11 2 6 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans Thin";
	panose-1:2 11 2 3 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans ExtraLight";
	panose-1:2 11 3 3 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans Condensed Light";
	panose-1:2 11 4 6 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans Light";
	panose-1:2 11 4 3 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans Condensed";
	panose-1:2 11 5 6 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans";
	panose-1:2 11 5 3 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans Condensed Medium";
	panose-1:2 11 6 6 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans Medium";
	panose-1:2 11 6 3 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Sans SemiBold";
	panose-1:2 11 7 3 5 2 3 0 2 3;}
@font-face
	{font-family:"IBM Plex Serif Thin";
	panose-1:2 6 2 3 5 4 6 0 2 3;}
@font-face
	{font-family:"IBM Plex Serif ExtraLight";
	panose-1:2 6 3 3 5 4 6 0 2 3;}
@font-face
	{font-family:"IBM Plex Serif Light";
	panose-1:2 6 4 3 5 4 6 0 2 3;}
@font-face
	{font-family:"IBM Plex Serif";
	panose-1:2 6 5 3 5 4 6 0 2 3;}
@font-face
	{font-family:"IBM Plex Serif Medium";
	panose-1:2 6 6 3 5 4 6 0 2 3;}
@font-face
	{font-family:"IBM Plex Serif SemiBold";
	panose-1:2 6 7 3 5 4 6 0 2 3;}
@font-face
	{font-family:"Inconsolata ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Expanded ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Condensed Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiCondensed Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiExpanded Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Expanded Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata ExtraExpanded Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata UltraExpanded Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata UltraCondensed";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata ExtraCondensed";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Condensed";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiCondensed";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Inconsolata;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiExpanded";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Expanded";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata ExtraExpanded";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata UltraExpanded";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Condensed Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiExpanded Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Expanded Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Condensed SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Expanded SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata UltraCondensed Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata ExtraCondensed Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Condensed Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiCondensed Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiExpanded Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Expanded Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata ExtraExpanded Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata UltraExpanded Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Condensed ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Expanded ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Condensed Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiCondensed Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata SemiExpanded Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata Expanded Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata ExtraExpanded Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Inconsolata UltraExpanded Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Ink Free";
	panose-1:3 8 4 2 0 5 0 0 0 0;}
@font-face
	{font-family:IrisUPC;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Iskoola Pota";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:Italianno;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:JasmineUPC;
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"Javanese Text";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Jokerman;
	panose-1:4 9 6 5 6 0 6 2 7 2;}
@font-face
	{font-family:"Josefin Sans Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Josefin Sans Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Josefin Sans";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Josefin Sans SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Josefin Sans Bold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Josefin Slab Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Josefin Slab Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Josefin Slab";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Josefin Slab SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Juice ITC";
	panose-1:4 4 4 3 4 0 2 2 2 2;}
@font-face
	{font-family:Jumble;
	panose-1:2 0 5 3 0 0 0 2 0 4;}
@font-face
	{font-family:Kalinga;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Karla ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Karla Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Karla;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Karla Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Karla ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Karla Tamil Inclined";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Karla Tamil Upright";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kermit Thin Condensed";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Thin";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Thin Expanded";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Extralight Condensed";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Extralight";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Extralight Expanded";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Light Condensed";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Light";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Light Expanded";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Condensed";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:Kermit;
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Expanded";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Semibold Condensed";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Semibold";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Semibold Expanded";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Extrabold Condensed";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Extrabold";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Kermit Extrabold Expanded";
	panose-1:2 15 5 3 4 0 0 6 0 3;}
@font-face
	{font-family:"Khmer UI";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Kigelia Light";
	panose-1:2 11 3 3 2 2 2 2 2 3;}
@font-face
	{font-family:Kigelia;
	panose-1:2 11 5 3 4 5 2 2 2 3;}
@font-face
	{font-family:"Kigelia Arabic Light";
	panose-1:2 11 3 3 2 2 2 2 2 3;}
@font-face
	{font-family:"Kigelia Arabic";
	panose-1:2 11 5 3 4 5 2 2 2 3;}
@font-face
	{font-family:"Klee One";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Klee One SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:KodchiangUPC;
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:Kokila;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Kristen ITC";
	panose-1:3 5 5 2 4 2 2 3 2 2;}
@font-face
	{font-family:"Krub ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Krub Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Krub;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Krub Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Krub SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Kunstler Script";
	panose-1:3 3 4 2 2 6 7 13 13 6;}
@font-face
	{font-family:Lalezar;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Lao UI";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Lato Thin";
	panose-1:2 15 5 2 2 2 4 3 2 3;}
@font-face
	{font-family:"Lato ExtraLight";
	panose-1:2 15 5 2 2 2 4 3 2 3;}
@font-face
	{font-family:"Lato Light";
	panose-1:2 15 5 2 2 2 4 3 2 3;}
@font-face
	{font-family:Lato;
	panose-1:2 15 5 2 2 2 4 3 2 3;}
@font-face
	{font-family:"Lato Medium";
	panose-1:2 15 5 2 2 2 4 3 2 3;}
@font-face
	{font-family:"Lato SemiBold";
	panose-1:2 15 5 2 2 2 4 3 2 3;}
@font-face
	{font-family:"Lato ExtraBold";
	panose-1:2 15 5 2 2 2 4 3 2 3;}
@font-face
	{font-family:"Lato Black";
	panose-1:2 15 5 2 2 2 4 3 2 3;}
@font-face
	{font-family:Leelawadee;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Leelawadee UI Semilight";
	panose-1:2 11 4 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Leelawadee UI";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Levenim MT";
	panose-1:2 1 5 2 6 1 1 1 1 1;}
@font-face
	{font-family:"Libre Barcode 128";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Barcode 128 Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Barcode 39";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Barcode 39 Extended";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Barcode 39 Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Barcode 39 Extended Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Barcode EAN13 Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Baskerville";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Franklin Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Franklin ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Franklin Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Franklin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Franklin Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Franklin SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Franklin ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Libre Franklin Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Ligconsolata;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:LilyUPC;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Livvic Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Livvic ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Livvic Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Livvic;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Livvic Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Livvic SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Livvic Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Lobster;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Lobster Two";
	panose-1:2 0 5 6 0 0 0 2 0 3;}
@font-face
	{font-family:Lora;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Lora Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Magneto;
	panose-1:4 3 8 5 5 8 2 2 13 2;}
@font-face
	{font-family:"Maiandra GD";
	panose-1:2 14 5 2 3 3 8 2 2 4;}
@font-face
	{font-family:"Mangal Pro";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Meddon;
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Merriweather Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Merriweather;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Merriweather Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Merriweather Sans Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Merriweather Sans";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Merriweather Sans ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Microsoft GothicNeo Light";
	panose-1:2 11 3 0 0 1 1 1 1 1;}
@font-face
	{font-family:"Microsoft GothicNeo";
	panose-1:2 11 5 0 0 1 1 1 1 1;}
@font-face
	{font-family:"Microsoft JhengHei UI Light";
	panose-1:2 11 3 4 3 5 4 4 2 4;}
@font-face
	{font-family:"Microsoft JhengHei UI";
	panose-1:2 11 6 4 3 5 4 4 2 4;}
@font-face
	{font-family:"Microsoft PhagsPa";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Microsoft Uighur";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Miriam;
	panose-1:2 11 5 2 5 1 1 1 1 1;}
@font-face
	{font-family:"Miriam Fixed";
	panose-1:2 11 5 9 5 1 1 1 1 1;}
@font-face
	{font-family:"Miriam Libre";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Mitr ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Mitr Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Mitr;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Mitr Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Mitr SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Modern Love";
	panose-1:4 9 8 5 8 16 5 2 6 1;}
@font-face
	{font-family:"Modern Love Caps";
	panose-1:4 7 8 5 8 16 1 2 10 1;}
@font-face
	{font-family:"Modern Love Grunge";
	panose-1:4 7 8 5 8 16 5 2 6 1;}
@font-face
	{font-family:"Montserrat Thin";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Montserrat ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Montserrat Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Montserrat;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Montserrat Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Montserrat SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Montserrat ExtraBold";
	panose-1:0 0 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Montserrat Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:MoolBoran;
	panose-1:2 11 1 0 1 1 1 1 1 1;}
@font-face
	{font-family:"Mr Gabe";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"MS Outlook";
	panose-1:5 1 1 0 1 0 0 0 0 0;}
@font-face
	{font-family:"MV Boli";
	panose-1:2 0 5 0 3 2 0 9 0 0;}
@font-face
	{font-family:"Mystical Woods Rough Script";
	panose-1:2 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Mystical Woods Smooth Script";
	panose-1:2 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nanum Brush Script";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nanum Pen";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:NanumGothic;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:NanumGothicExtraBold;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:NanumGothicCoding;
	panose-1:2 13 0 9 0 0 0 0 0 0;}
@font-face
	{font-family:NanumMyeongjo;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:NanumMyeongjoExtraBold;
	panose-1:2 2 6 3 2 1 1 2 1 1;}
@font-face
	{font-family:Narkisim;
	panose-1:2 14 5 2 5 1 1 1 1 1;}
@font-face
	{font-family:"Neue Haas Grotesk Text Pro";
	panose-1:2 11 5 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Niagara Engraved";
	panose-1:4 2 5 2 7 7 3 3 2 2;}
@font-face
	{font-family:"Niagara Solid";
	panose-1:4 2 5 2 7 7 2 2 2 2;}
@font-face
	{font-family:Nina;
	panose-1:2 11 6 6 3 5 4 4 2 4;}
@font-face
	{font-family:"Nirmala Text Semilight";
	panose-1:2 11 4 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Nirmala Text";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Nirmala UI Semilight";
	panose-1:2 11 4 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Nirmala UI";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Nordique Inline";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Music";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans AnatoHiero";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Avestan";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Bassa Vah";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Bhaiksuki";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Brahmi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Buginese";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Buhid";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Carian";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans CaucAlban";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Chakma";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Coptic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Cuneiform";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Cypriot";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Deseret";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari ExtraLight";
	panose-1:2 11 3 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari Medium";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari SemiBold";
	panose-1:2 11 7 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari ExtraBold";
	panose-1:2 11 9 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari Black";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari UI Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari UI Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari UI";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari UI Medium";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Devanagari UI Black";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Duployan";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans EgyptHiero";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Elbasan";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Elymaic";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans Glagolitic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gothic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Grantha";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati ExtraLight";
	panose-1:2 11 3 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati Medium";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati SemiBold";
	panose-1:2 11 7 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati ExtraBold";
	panose-1:2 11 9 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati Black";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati UI Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati UI Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati UI";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati UI Medium";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati UI SemiBold";
	panose-1:2 11 7 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati UI ExtraBold";
	panose-1:2 11 9 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gujarati UI Black";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Gunjala Gondi";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans Hanunoo";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Hatran";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans ImpAramaic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Indic Siyaq Numbers";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans InsPahlavi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans InsParthi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Javanese";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kaithi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Kharoshthi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Khojki";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Khudawadi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Lepcha";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Limbu";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Linear A";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Linear B";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Lycian";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Lydian";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Mahajani";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Mandaic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Manichaean";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Marchen";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Masaram Gondi";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans Math";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Mayan Numerals";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Mende Kikakui";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Meroitic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Miao";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Modi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Mongolian";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Mro";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Multani";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar UI Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar UI ExtraLight";
	panose-1:2 11 3 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar UI Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar UI";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar UI Medium";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar UI SemiBold";
	panose-1:2 11 7 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar UI ExtraBold";
	panose-1:2 11 9 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Myanmar UI Black";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Nabataean";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans NewTaiLue";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Newa";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Nushu";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Ogham";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans OldHung";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Old Italic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans OldNorArab";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Old Permic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans OldPersian";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans OldSogdian";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans OldSouArab";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Old Turkic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Oriya UI Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans Oriya UI";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans Oriya UI Blk";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans Osage";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Osmanya";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Pahawh Hmong";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Palmyrene";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans PauCinHau";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans PhagsPa";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Phoenician";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans PsaPahlavi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Rejang";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Runic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Samaritan";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Saurashtra";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Sharada";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Shavian";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Siddham";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Sogdian";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Soyombo";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Syloti Nagri";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Symbols2";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Syriac Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Syriac";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Syriac Black";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Tagbanwa";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Tai Le";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Tai Viet";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Takri";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Tamil Supplement";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans Thai Looped Thin";
	panose-1:2 11 2 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Thai Looped ExtLight";
	panose-1:2 11 3 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Thai Looped Light";
	panose-1:2 11 4 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Thai Looped Regular";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Thai Looped Medium";
	panose-1:2 11 6 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Thai Looped Semibold";
	panose-1:2 11 7 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Thai Looped Bold";
	panose-1:2 11 8 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Thai Looped Extrabold";
	panose-1:2 11 9 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Thai Looped Black";
	panose-1:2 11 10 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Tifinagh";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Sans Tirhuta";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Ugaritic";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Vai";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Wancho";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans WarangCiti";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Yi";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Sans Zanabazar";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Noto Serif";
	panose-1:2 2 6 0 6 5 0 2 2 0;}
@font-face
	{font-family:"Noto Serif Ahom";
	panose-1:2 2 5 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Balinese";
	panose-1:2 2 5 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Dogra";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Noto Serif Grantha";
	panose-1:2 2 5 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Serif Tangut";
	panose-1:2 2 5 2 6 5 5 2 2 4;}
@font-face
	{font-family:"Noto Traditional Nushu";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Nunito;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito Sans ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito Sans Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito Sans";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito Sans SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito Sans ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Nunito Sans Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:OCRB;
	panose-1:2 11 6 9 2 2 2 2 2 4;}
@font-face
	{font-family:"Old English Text MT";
	panose-1:3 4 9 2 4 5 8 3 8 6;}
@font-face
	{font-family:"Open Sans Light";
	panose-1:2 11 3 6 3 5 4 2 2 4;}
@font-face
	{font-family:"Open Sans";
	panose-1:2 11 6 6 3 5 4 2 2 4;}
@font-face
	{font-family:"Open Sans SemiBold";
	panose-1:2 11 7 6 3 8 4 2 2 4;}
@font-face
	{font-family:"Open Sans ExtraBold";
	panose-1:2 11 9 6 3 8 4 2 2 4;}
@font-face
	{font-family:Oranienbaum;
	panose-1:2 0 5 6 8 0 0 2 0 3;}
@font-face
	{font-family:"Oswald ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Oswald Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Oswald;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Oswald Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Oswald SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Oxygen Light";
	panose-1:2 0 3 3 0 0 0 0 0 0;}
@font-face
	{font-family:Oxygen;
	panose-1:2 0 5 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Oxygen Mono";
	panose-1:2 0 5 9 3 0 0 9 0 4;}
@font-face
	{font-family:Pacifico;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Palace Script MT";
	panose-1:3 3 3 2 2 6 7 12 11 5;}
@font-face
	{font-family:"Palanquin Thin";
	panose-1:2 11 0 4 2 2 3 2 2 4;}
@font-face
	{font-family:"Palanquin ExtraLight";
	panose-1:2 11 0 4 2 2 3 2 2 4;}
@font-face
	{font-family:"Palanquin Light";
	panose-1:2 11 0 4 2 2 3 2 2 4;}
@font-face
	{font-family:Palanquin;
	panose-1:2 11 0 4 2 2 3 2 2 4;}
@font-face
	{font-family:"Palanquin Medium";
	panose-1:2 11 0 4 2 2 3 2 2 4;}
@font-face
	{font-family:"Palanquin SemiBold";
	panose-1:2 11 0 4 2 2 3 2 2 4;}
@font-face
	{font-family:Parchment;
	panose-1:3 4 6 2 4 7 8 4 8 4;}
@font-face
	{font-family:"Patrick Hand";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Patrick Hand SC";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Petit Formal Script";
	panose-1:3 2 6 2 4 8 7 8 11 6;}
@font-face
	{font-family:Playbill;
	panose-1:4 5 6 3 0 6 2 2 2 2;}
@font-face
	{font-family:"Playfair Display";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Playfair Display Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Playfair Display SC";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Playfair Display SC Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Poiret One";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Poor Richard";
	panose-1:2 8 5 2 5 5 5 2 7 2;}
@font-face
	{font-family:"Poppins Thin";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Poppins ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Poppins Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Poppins;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Poppins Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Poppins SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Poppins ExtraBold";
	panose-1:0 0 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Poppins Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:Posterama;
	panose-1:2 11 5 4 2 2 0 2 0 0;}
@font-face
	{font-family:"Pridi ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Pridi Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Pridi;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Pridi Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Pridi SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:Pristina;
	panose-1:3 6 4 2 4 4 6 8 2 4;}
@font-face
	{font-family:"Prompt Thin";
	panose-1:0 0 2 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Prompt ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Prompt Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Prompt;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Prompt Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Prompt SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Prompt ExtraBold";
	panose-1:0 0 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Prompt Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:Quattrocento;
	panose-1:2 2 5 2 3 0 0 0 4 4;}
@font-face
	{font-family:"Quattrocento Sans";
	panose-1:2 11 5 2 5 0 0 2 0 3;}
@font-face
	{font-family:Questrial;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Quire Sans Light";
	panose-1:2 11 3 2 4 4 0 2 0 3;}
@font-face
	{font-family:"Quire Sans";
	panose-1:2 11 5 2 4 4 0 2 0 3;}
@font-face
	{font-family:"Quire Sans Pro Light";
	panose-1:2 11 3 2 4 4 0 2 0 3;}
@font-face
	{font-family:"Rage Italic";
	panose-1:3 7 5 2 4 5 7 7 3 4;}
@font-face
	{font-family:"Raleway Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Raleway ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Raleway Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Raleway;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Raleway Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Raleway SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Raleway ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Raleway Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Rastanty Cortez";
	panose-1:2 0 5 6 0 0 0 2 0 3;}
@font-face
	{font-family:Ravie;
	panose-1:4 4 8 5 5 8 9 2 6 2;}
@font-face
	{font-family:"Reem Kufi";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Thin";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Condensed Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Light";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Condensed";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Roboto;
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Condensed Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Medium";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Black";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Mono Thin";
	panose-1:0 0 0 9 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Mono Light";
	panose-1:0 0 0 9 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Mono";
	panose-1:0 0 0 9 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Mono Medium";
	panose-1:0 0 0 9 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Serif 20pt Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Serif 20pt ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Serif 20pt Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Serif 20pt";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Serif 20pt Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Serif 20pt SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Serif 20pt ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Serif 20pt Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Slab Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Slab ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Slab Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Slab";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Slab Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Slab SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Slab ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Roboto Slab Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Rockwell Nova Cond Light";
	panose-1:2 6 3 6 2 2 5 2 4 3;}
@font-face
	{font-family:"Rockwell Nova Light";
	panose-1:2 6 3 3 2 2 5 2 4 3;}
@font-face
	{font-family:"Rockwell Nova Cond";
	panose-1:2 6 5 6 2 2 5 2 4 3;}
@font-face
	{font-family:"Rockwell Nova";
	panose-1:2 6 5 3 2 2 5 2 4 3;}
@font-face
	{font-family:"Rockwell Nova Extra Bold";
	panose-1:2 6 9 3 2 2 5 2 4 3;}
@font-face
	{font-family:Rod;
	panose-1:2 3 5 9 5 1 1 1 1 1;}
@font-face
	{font-family:"Sabon Next LT";
	panose-1:2 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:Sacramento;
	panose-1:2 0 5 7 0 0 0 2 0 0;}
@font-face
	{font-family:"Sagona ExtraLight";
	panose-1:2 2 3 3 5 5 5 2 2 4;}
@font-face
	{font-family:Sagona;
	panose-1:2 1 0 4 4 1 1 1 1 3;}
@font-face
	{font-family:"Sagona Book";
	panose-1:2 2 5 3 5 5 5 2 2 4;}
@font-face
	{font-family:"Sakkal Majalla";
	panose-1:2 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sans Serif Collection";
	panose-1:2 11 5 2 4 5 4 2 2 4;}
@font-face
	{font-family:"Sanskrit Text";
	panose-1:2 2 5 3 5 4 5 2 3 4;}
@font-face
	{font-family:"Script MT Bold";
	panose-1:3 4 6 2 4 6 7 8 9 4;}
@font-face
	{font-family:Seaford;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Seaford Display";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Secular One";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Marker";
	panose-1:3 8 6 2 4 3 2 2 2 4;}
@font-face
	{font-family:"Segoe Pro Light";
	panose-1:2 11 3 2 4 5 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro Cond";
	panose-1:2 11 5 6 4 5 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro";
	panose-1:2 11 5 2 4 5 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro Semibold";
	panose-1:2 11 7 2 4 5 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro Black";
	panose-1:2 11 10 2 4 5 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro Display Light";
	panose-1:2 11 3 2 4 5 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro Display";
	panose-1:2 11 5 2 4 5 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro Display Semibold";
	panose-1:2 11 7 2 4 5 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro Display SemiLight";
	panose-1:2 11 4 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe Pro SemiLight";
	panose-1:2 11 4 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe Sans Display Hairline";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Display Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Display Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Display Semilight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Display";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Display Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Display ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Display Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Small Hairline";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Small Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Small Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Small Semilight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Small";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Small Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Small ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Small Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Text Hairline";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Text Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Text Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Text Semilight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Text Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Text ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Sans Text Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Banner Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Banner Semilight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Banner";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Banner Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Display Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Display Semilight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Display";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Display Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Text Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Text Semilight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Serif Text Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe UI Light";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe UI Semilight";
	panose-1:2 11 4 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe UI";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe UI Semibold";
	panose-1:2 11 7 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe UI Black";
	panose-1:2 11 10 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe UI Emoji";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe UI Emoji L";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Segoe UI Variable Display Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe UI Variable Display";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe UI Variable Small Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe UI Variable Small";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe UI Variable Text Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe UI Variable Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Segoe Xbox Symbol";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Selawik Light";
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:Selawik;
	panose-1:2 11 5 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Selawik Semibold";
	panose-1:2 11 7 2 4 2 4 2 2 3;}
@font-face
	{font-family:"Shadows Into Light Two";
	panose-1:2 0 5 6 0 0 0 2 0 4;}
@font-face
	{font-family:"Shonar Bangla";
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"Showcard Gothic";
	panose-1:4 2 9 4 2 1 2 2 6 4;}
@font-face
	{font-family:"Simplified Arabic";
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"Simplified Arabic Fixed";
	panose-1:2 7 3 9 2 2 5 2 4 4;}
@font-face
	{font-family:"Sitka Banner";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Banner Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Display";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Display Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Heading";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Heading Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Small";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Small Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Subheading";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Subheading Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Text";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Sitka Text Semibold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Skeena;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Skeena Display";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Snap ITC";
	panose-1:4 4 10 7 6 10 2 2 2 2;}
@font-face
	{font-family:"Source Code Pro ExtraLight";
	panose-1:2 11 3 9 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Code Pro Light";
	panose-1:2 11 4 9 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Code Pro";
	panose-1:2 11 5 9 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Code Pro Medium";
	panose-1:2 11 5 9 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Code Pro Semibold";
	panose-1:2 11 6 9 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Code Pro Black";
	panose-1:2 11 8 9 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Sans Pro ExtraLight";
	panose-1:2 11 3 3 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Sans Pro Light";
	panose-1:2 11 4 3 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Sans Pro";
	panose-1:2 11 5 3 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Sans Pro SemiBold";
	panose-1:2 11 6 3 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Sans Pro Black";
	panose-1:2 11 8 3 3 4 3 2 2 4;}
@font-face
	{font-family:"Source Serif Pro ExtraLight";
	panose-1:2 4 2 3 5 4 5 2 2 4;}
@font-face
	{font-family:"Source Serif Pro Light";
	panose-1:2 4 3 3 5 4 5 2 2 4;}
@font-face
	{font-family:"Source Serif Pro";
	panose-1:2 4 6 3 5 4 5 2 2 4;}
@font-face
	{font-family:"Source Serif Pro SemiBold";
	panose-1:2 4 7 3 5 4 5 2 2 4;}
@font-face
	{font-family:"Source Serif Pro Black";
	panose-1:2 4 9 3 5 4 5 2 2 4;}
@font-face
	{font-family:"Speak Pro Light";
	panose-1:2 11 3 4 2 1 1 2 1 2;}
@font-face
	{font-family:"Speak Pro";
	panose-1:2 11 5 4 2 1 1 2 1 2;}
@font-face
	{font-family:Staatliches;
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:STCaiyun;
	panose-1:2 1 8 0 4 1 1 1 1 1;}
@font-face
	{font-family:STFangsong;
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:STKaiti;
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:STXihei;
	panose-1:2 1 6 0 4 1 1 1 1 1;}
@font-face
	{font-family:"Suez One";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Tempus Sans ITC";
	panose-1:4 2 4 4 3 0 7 2 2 2;}
@font-face
	{font-family:Tenorite;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Tenorite Display";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"The Hand Light";
	panose-1:3 7 3 2 3 5 2 2 2 4;}
@font-face
	{font-family:"The Hand";
	panose-1:3 7 5 2 3 5 2 2 2 4;}
@font-face
	{font-family:"The Hand Black";
	panose-1:3 7 9 2 3 5 2 2 2 4;}
@font-face
	{font-family:"The Hand Extrablack";
	panose-1:3 7 10 2 3 5 2 2 2 4;}
@font-face
	{font-family:"The Serif Hand Light";
	panose-1:3 7 3 2 3 5 2 2 2 4;}
@font-face
	{font-family:"The Serif Hand";
	panose-1:3 7 5 2 3 5 2 2 2 4;}
@font-face
	{font-family:"The Serif Hand Black";
	panose-1:3 7 9 2 3 5 2 2 2 4;}
@font-face
	{font-family:"The Serif Hand Extrablack";
	panose-1:3 7 11 2 3 5 2 2 2 4;}
@font-face
	{font-family:"Tisa Offc Serif Pro Thin";
	panose-1:2 1 4 4 3 1 1 1 1 2;}
@font-face
	{font-family:"Tisa Offc Serif Pro";
	panose-1:2 1 5 4 3 1 1 2 1 2;}
@font-face
	{font-family:"Titillium Web ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Titillium Web Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Titillium Web";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Titillium Web SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Titillium Web Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Trade Gothic Inline";
	panose-1:2 11 5 4 3 2 3 2 2 4;}
@font-face
	{font-family:"Trade Gothic Next Light";
	panose-1:2 11 4 3 4 3 3 2 0 4;}
@font-face
	{font-family:"Trade Gothic Next Cond";
	panose-1:2 11 5 6 4 3 3 2 0 4;}
@font-face
	{font-family:"Trade Gothic Next";
	panose-1:2 11 5 3 4 3 3 2 0 4;}
@font-face
	{font-family:"Trade Gothic Next HvyCd";
	panose-1:2 11 9 6 4 3 3 2 0 4;}
@font-face
	{font-family:"Trade Gothic Next Heavy";
	panose-1:2 11 9 3 4 3 3 2 0 4;}
@font-face
	{font-family:"Trade Gothic Next Rounded";
	panose-1:2 15 5 3 4 3 3 2 0 4;}
@font-face
	{font-family:"Traditional Arabic";
	panose-1:2 2 6 3 5 4 5 2 3 4;}
@font-face
	{font-family:"Trirong Thin";
	panose-1:0 0 2 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Trirong ExtraLight";
	panose-1:0 0 3 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Trirong Light";
	panose-1:0 0 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:Trirong;
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Trirong Medium";
	panose-1:0 0 6 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Trirong SemiBold";
	panose-1:0 0 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Trirong ExtraBold";
	panose-1:0 0 9 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Trirong Black";
	panose-1:0 0 10 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Ubuntu Light";
	panose-1:2 11 3 4 3 6 2 3 2 4;}
@font-face
	{font-family:"Ubuntu Condensed";
	panose-1:2 11 5 6 3 6 2 3 2 4;}
@font-face
	{font-family:Ubuntu;
	panose-1:2 11 5 4 3 6 2 3 2 4;}
@font-face
	{font-family:"Ubuntu Medium";
	panose-1:2 11 6 4 3 6 2 3 2 4;}
@font-face
	{font-family:"Ubuntu Mono";
	panose-1:2 11 5 9 3 6 2 3 2 4;}
@font-face
	{font-family:"UD Digi Kyokasho N-B";
	panose-1:2 2 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"UD Digi Kyokasho N-R";
	panose-1:2 2 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"UD Digi Kyokasho NK-B";
	panose-1:2 2 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"UD Digi Kyokasho NK-R";
	panose-1:2 2 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"UD Digi Kyokasho NP-B";
	panose-1:2 2 7 0 0 0 0 0 0 0;}
@font-face
	{font-family:"UD Digi Kyokasho NP-R";
	panose-1:2 2 4 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Univers Condensed Light";
	panose-1:2 11 3 6 2 2 2 4 2 4;}
@font-face
	{font-family:"Univers Light";
	panose-1:2 11 4 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Univers Condensed";
	panose-1:2 11 5 6 2 2 2 5 2 4;}
@font-face
	{font-family:Univers;
	panose-1:2 11 5 3 2 2 2 2 2 4;}
@font-face
	{font-family:"Urdu Typesetting";
	panose-1:3 2 4 2 4 4 6 3 2 3;}
@font-face
	{font-family:Utsaah;
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:Vani;
	panose-1:2 4 5 2 5 4 5 2 3 3;}
@font-face
	{font-family:"Varela Round";
	panose-1:0 0 5 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Verdana Pro Cond Light";
	panose-1:2 11 3 6 3 5 4 4 2 4;}
@font-face
	{font-family:"Verdana Pro Light";
	panose-1:2 11 3 4 3 5 4 4 2 4;}
@font-face
	{font-family:"Verdana Pro Cond";
	panose-1:2 11 6 6 3 5 4 4 2 4;}
@font-face
	{font-family:"Verdana Pro";
	panose-1:2 11 6 4 3 5 4 4 2 4;}
@font-face
	{font-family:"Verdana Pro Cond Semibold";
	panose-1:2 11 7 6 3 5 4 4 2 4;}
@font-face
	{font-family:"Verdana Pro Semibold";
	panose-1:2 11 7 4 3 5 4 4 2 4;}
@font-face
	{font-family:"Verdana Pro Cond Black";
	panose-1:2 11 10 6 3 5 4 4 2 4;}
@font-face
	{font-family:"Verdana Pro Black";
	panose-1:2 11 10 4 3 5 4 4 2 4;}
@font-face
	{font-family:Vijaya;
	panose-1:2 2 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"Viner Hand ITC";
	panose-1:3 7 5 2 3 5 2 2 2 3;}
@font-face
	{font-family:Vivaldi;
	panose-1:3 2 6 2 5 5 6 9 8 4;}
@font-face
	{font-family:"Vladimir Script";
	panose-1:3 5 4 2 4 4 7 7 3 5;}
@font-face
	{font-family:"Walbaum Display Light";
	panose-1:2 7 3 3 9 7 3 2 3 3;}
@font-face
	{font-family:"Walbaum Display";
	panose-1:2 7 5 3 9 7 3 2 3 3;}
@font-face
	{font-family:"Walbaum Display SemiBold";
	panose-1:2 7 7 3 9 7 3 2 3 3;}
@font-face
	{font-family:"Walbaum Display Heavy";
	panose-1:2 7 10 3 9 7 3 2 3 3;}
@font-face
	{font-family:"Walbaum Heading";
	panose-1:2 7 3 3 9 7 3 2 3 3;}
@font-face
	{font-family:"Walbaum Text";
	panose-1:2 7 5 3 8 7 3 2 3 3;}
@font-face
	{font-family:Wandohope;
	panose-1:2 3 6 3 0 0 0 0 0 0;}
@font-face
	{font-family:"Work Sans Thin";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Work Sans ExtraLight";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Work Sans Light";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Work Sans";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Work Sans Medium";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Work Sans SemiBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Work Sans ExtraBold";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:"Work Sans Black";
	panose-1:0 0 0 0 0 0 0 0 0 0;}
@font-face
	{font-family:Yesteryear;
	panose-1:3 2 8 2 4 6 7 7 8 2;}
@font-face
	{font-family:"OldGreekSerif Normal";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"StplGaramondAkzente Normal";
	panose-1:2 11 6 4 2 2 2 2 2 4;}
@font-face
	{font-family:"\@Yu Gothic";
	panose-1:2 11 4 0 0 0 0 0 0 0;}
 /* Style Definitions */
 p.MsoNormal, li.MsoNormal, div.MsoNormal
	{margin:0cm;
	text-align:justify;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;}
h1
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:35.4pt;
	text-align:center;
	text-indent:-35.4pt;
	line-height:11.6pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.5pt;
	font-family:"StplGaramond",serif;}
h2
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:70.8pt;
	text-align:center;
	text-indent:-35.4pt;
	line-height:10.6pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:9.5pt;
	font-family:"StplGaramond",serif;}
h3
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:106.2pt;
	text-align:center;
	text-indent:-35.4pt;
	line-height:9.6pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:9.0pt;
	font-family:"StplGaramond",serif;}
h4
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:141.6pt;
	text-align:center;
	text-indent:-35.4pt;
	line-height:8.6pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:7.5pt;
	font-family:"StplGaramond",serif;}
h5
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:177.0pt;
	text-align:justify;
	text-indent:-35.4pt;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;}
h6
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:212.4pt;
	text-align:justify;
	text-indent:-35.4pt;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;
	font-weight:normal;
	text-decoration:underline;}
p.MsoHeading7, li.MsoHeading7, div.MsoHeading7
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:247.8pt;
	text-align:justify;
	text-indent:-35.4pt;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;
	font-style:italic;}
p.MsoHeading8, li.MsoHeading8, div.MsoHeading8
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:283.2pt;
	text-align:justify;
	text-indent:-35.4pt;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;
	font-style:italic;}
p.MsoHeading9, li.MsoHeading9, div.MsoHeading9
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:318.6pt;
	text-align:justify;
	text-indent:-35.4pt;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;
	font-style:italic;}
p.MsoNormalIndent, li.MsoNormalIndent, div.MsoNormalIndent
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:35.4pt;
	text-align:justify;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;}
p.MsoFootnoteText, li.MsoFootnoteText, div.MsoFootnoteText
	{margin:0cm;
	text-align:justify;
	line-height:7.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:7.0pt;
	font-family:"StplGaramond",serif;}
p.MsoCommentText, li.MsoCommentText, div.MsoCommentText
	{margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;}
p.MsoHeader, li.MsoHeader, div.MsoHeader
	{margin:0cm;
	text-align:justify;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;}
p.MsoFooter, li.MsoFooter, div.MsoFooter
	{margin:0cm;
	text-align:justify;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;}
span.MsoFootnoteReference
	{position:relative;
	top:-3.0pt;}
p.MsoListBullet, li.MsoListBullet, div.MsoListBullet
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:18.0pt;
	text-align:justify;
	text-indent:-18.0pt;
	line-height:-73%;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;}
p.MsoBodyText, li.MsoBodyText, div.MsoBodyText
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:6.0pt;
	margin-left:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"StplGaramond",serif;}
p.MsoBodyTextIndent, li.MsoBodyTextIndent, div.MsoBodyTextIndent
	{margin-top:0cm;
	margin-right:0cm;
	margin-bottom:6.0pt;
	margin-left:14.15pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"StplGaramond",serif;}
a:link, span.MsoHyperlink
	{color:blue;
	text-decoration:underline;}
a:visited, span.MsoHyperlinkFollowed
	{color:#954F72;
	text-decoration:underline;}
p.HalbeLeerzeile, li.HalbeLeerzeile, div.HalbeLeerzeile
	{mso-style-name:HalbeLeerzeile;
	margin:0cm;
	text-align:justify;
	line-height:5.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;}
p.Bogennorm, li.Bogennorm, div.Bogennorm
	{mso-style-name:Bogennorm;
	margin:0cm;
	text-align:justify;
	line-height:7.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:6.5pt;
	font-family:"StplGaramond",serif;
	color:white;
	letter-spacing:.5pt;}
p.bogenzahl, li.bogenzahl, div.bogenzahl
	{mso-style-name:bogenzahl;
	margin:0cm;
	text-align:justify;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:6.5pt;
	font-family:"StplGaramondAkzente",serif;
	color:white;}
p.Funotenlinie, li.Funotenlinie, div.Funotenlinie
	{mso-style-name:Fußnotenlinie;
	margin:0cm;
	text-align:justify;
	line-height:7.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:7.0pt;
	font-family:"StplGaramond",serif;}
p.koltitel, li.koltitel, div.koltitel
	{mso-style-name:koltitel;
	margin:0cm;
	text-align:justify;
	line-height:8.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.0pt;
	font-family:"StempelGaramond RomanSC",serif;
	color:white;}
p.Autorfu, li.Autorfu, div.Autorfu
	{mso-style-name:Autorfuß;
	margin:0cm;
	text-align:justify;
	line-height:8.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:6.0pt;
	font-family:"StplGaramond",serif;
	color:white;
	font-style:italic;}
p.Artikeltext, li.Artikeltext, div.Artikeltext
	{mso-style-name:Artikeltext;
	margin:0cm;
	text-align:justify;
	line-height:8.6pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.0pt;
	font-family:"NewCenturySchlbk",serif;}
p.artikel, li.artikel, div.artikel
	{mso-style-name:artikel;
	margin:0cm;
	line-height:8.4pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.0pt;
	font-family:"NewCenturySchlbk",serif;}
p.jokol, li.jokol, div.jokol
	{mso-style-name:jokol;
	margin:0cm;
	text-align:justify;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:4.0pt;
	font-family:"StplGaramond",serif;
	color:white;
	letter-spacing:-1.5pt;}
p.jofu, li.jofu, div.jofu
	{mso-style-name:jofuß;
	margin:0cm;
	text-align:justify;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:4.0pt;
	font-family:"StplGaramond",serif;
	color:white;
	letter-spacing:-1.5pt;}
span.lemma
	{mso-style-name:lemma;
	font-weight:bold;}
span.lemmawiederholung
	{mso-style-name:lemmawiederholung;
	font-family:PiEdit-K;
	color:white;}
span.jofu2
	{mso-style-name:jofuß2;
	font-family:PiEdit-K;
	color:white;
	letter-spacing:-2.0pt;}
p.j, li.j, div.j
	{mso-style-name:j;
	margin:0cm;
	text-align:justify;
	text-indent:6.5pt;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;}
p.Vorrede, li.Vorrede, div.Vorrede
	{mso-style-name:Vorrede;
	margin:0cm;
	text-align:justify;
	text-indent:21.25pt;
	line-height:12.8pt;
	background:white;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;}
p.Regest, li.Regest, div.Regest
	{mso-style-name:Regest;
	margin-top:18.5pt;
	margin-right:0cm;
	margin-bottom:5.5pt;
	margin-left:29.75pt;
	text-align:justify;
	text-indent:-21.25pt;
	line-height:15.5pt;
	background:white;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.5pt;
	font-family:"Times New Roman",serif;
	font-style:italic;}
span.FormatvorlageTimesNewRoman
	{mso-style-name:"Formatvorlage Times New Roman";
	font-family:"StplGaramond",serif;}
p.Funotenrnd5, li.Funotenrnd5, div.Funotenrnd5
	{mso-style-name:FuÀÀnotenrnd5;
	margin:0cm;
	text-align:justify;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;
	letter-spacing:-.15pt;}
span.FormatInh8
	{mso-style-name:"FormatInh\[8\]";}
span.FormatInh5
	{mso-style-name:"FormatInh\[5\]";}
span.FormatInh6
	{mso-style-name:"FormatInh\[6\]";}
span.FormatInh2
	{mso-style-name:"FormatInh\[2\]";
	font-family:"Garamond Antiqua",serif;}
span.FormatInh7
	{mso-style-name:"FormatInh\[7\]";}
p.AbsNrRech1, li.AbsNrRech1, div.AbsNrRech1
	{mso-style-name:"AbsNrRech\[1\]";
	margin:0cm;
	text-indent:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRech2, li.AbsNrRech2, div.AbsNrRech2
	{mso-style-name:"AbsNrRech\[2\]";
	margin:0cm;
	text-indent:72.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
span.FormatInh3
	{mso-style-name:"FormatInh\[3\]";
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRech3, li.AbsNrRech3, div.AbsNrRech3
	{mso-style-name:"AbsNrRech\[3\]";
	margin:0cm;
	text-indent:108.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRech4, li.AbsNrRech4, div.AbsNrRech4
	{mso-style-name:"AbsNrRech\[4\]";
	margin:0cm;
	text-indent:144.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRech5, li.AbsNrRech5, div.AbsNrRech5
	{mso-style-name:"AbsNrRech\[5\]";
	margin:0cm;
	text-indent:180.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRech6, li.AbsNrRech6, div.AbsNrRech6
	{mso-style-name:"AbsNrRech\[6\]";
	margin:0cm;
	text-indent:216.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRech7, li.AbsNrRech7, div.AbsNrRech7
	{mso-style-name:"AbsNrRech\[7\]";
	margin:0cm;
	text-indent:252.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRech8, li.AbsNrRech8, div.AbsNrRech8
	{mso-style-name:"AbsNrRech\[8\]";
	margin:0cm;
	text-indent:288.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.FormatInh1, li.FormatInh1, div.FormatInh1
	{mso-style-name:"FormatInh\[1\]";
	margin:0cm;
	page-break-after:avoid;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
span.FormatInh4
	{mso-style-name:"FormatInh\[4\]";
	font-weight:bold;
	font-style:italic;}
span.Bblgraphie
	{mso-style-name:Bblgraphie;}
span.MarkInhalt
	{mso-style-name:MarkInhalt;}
p.Document1, li.Document1, div.Document1
	{mso-style-name:"Document 1";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document2, li.Document2, div.Document2
	{mso-style-name:"Document 2";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document3, li.Document3, div.Document3
	{mso-style-name:"Document 3";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document4, li.Document4, div.Document4
	{mso-style-name:"Document 4";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document5, li.Document5, div.Document5
	{mso-style-name:"Document 5";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document6, li.Document6, div.Document6
	{mso-style-name:"Document 6";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document7, li.Document7, div.Document7
	{mso-style-name:"Document 7";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document8, li.Document8, div.Document8
	{mso-style-name:"Document 8";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
span.FormatInh80
	{mso-style-name:"FormatInh 8";}
span.FormatInh50
	{mso-style-name:"FormatInh 5";}
span.FormatInh60
	{mso-style-name:"FormatInh 6";}
span.FormatInh20
	{mso-style-name:"FormatInh 2";
	font-family:"Garamond Antiqua",serif;}
span.FormatInh70
	{mso-style-name:"FormatInh 7";}
p.AbsNrRechts1, li.AbsNrRechts1, div.AbsNrRechts1
	{mso-style-name:"AbsNrRechts 1";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	text-indent:-9.25pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRechts2, li.AbsNrRechts2, div.AbsNrRechts2
	{mso-style-name:"AbsNrRechts 2";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:72.0pt;
	text-indent:-13.1pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
span.FormatInh30
	{mso-style-name:"FormatInh 3";
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRechts3, li.AbsNrRechts3, div.AbsNrRechts3
	{mso-style-name:"AbsNrRechts 3";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:108.0pt;
	text-indent:-10.85pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRechts4, li.AbsNrRechts4, div.AbsNrRechts4
	{mso-style-name:"AbsNrRechts 4";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:144.0pt;
	text-indent:-10.3pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRechts5, li.AbsNrRechts5, div.AbsNrRechts5
	{mso-style-name:"AbsNrRechts 5";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:180.0pt;
	text-indent:-15.05pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRechts6, li.AbsNrRechts6, div.AbsNrRechts6
	{mso-style-name:"AbsNrRechts 6";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:216.0pt;
	text-indent:-14.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRechts7, li.AbsNrRechts7, div.AbsNrRechts7
	{mso-style-name:"AbsNrRechts 7";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:252.0pt;
	text-indent:-9.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.AbsNrRechts8, li.AbsNrRechts8, div.AbsNrRechts8
	{mso-style-name:"AbsNrRechts 8";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:288.0pt;
	text-indent:-11.15pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.FormatInh10, li.FormatInh10, div.FormatInh10
	{mso-style-name:"FormatInh 1";
	margin:0cm;
	page-break-after:avoid;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
span.FormatInh40
	{mso-style-name:"FormatInh 4";
	font-weight:bold;
	font-style:italic;}
span.Funoten
	{mso-style-name:FuÀÀnoten;
	font-family:"Courier New";}
p.Document10, li.Document10, div.Document10
	{mso-style-name:"Document\[1\]";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	text-indent:-36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document20, li.Document20, div.Document20
	{mso-style-name:"Document\[2\]";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:72.0pt;
	text-indent:-36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document30, li.Document30, div.Document30
	{mso-style-name:"Document\[3\]";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:108.0pt;
	text-indent:-36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document40, li.Document40, div.Document40
	{mso-style-name:"Document\[4\]";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:144.0pt;
	text-indent:-36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document50, li.Document50, div.Document50
	{mso-style-name:"Document\[5\]";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:180.0pt;
	text-indent:-36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document60, li.Document60, div.Document60
	{mso-style-name:"Document\[6\]";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:216.0pt;
	text-indent:-36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document70, li.Document70, div.Document70
	{mso-style-name:"Document\[7\]";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:252.0pt;
	text-indent:-36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.Document80, li.Document80, div.Document80
	{mso-style-name:"Document\[8\]";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:288.0pt;
	text-indent:-36.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
p.footnotetex, li.footnotetex, div.footnotetex
	{mso-style-name:"footnote tex";
	margin:0cm;
	text-align:justify;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;
	letter-spacing:-.1pt;}
span.footnoteref
	{mso-style-name:"footnote ref";
	font-family:"Times New Roman",serif;
	vertical-align:super;}
p.toa, li.toa, div.toa
	{mso-style-name:toa;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Garamond Antiqua",serif;}
span.EquationCaption
	{mso-style-name:"_Equation Caption";}
span.Typewriter
	{mso-style-name:Typewriter;
	font-family:"Courier New";}
p.DefinitionTerm, li.DefinitionTerm, div.DefinitionTerm
	{mso-style-name:"Definition Term";
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Times New Roman",serif;}
p.DefinitionList, li.DefinitionList, div.DefinitionList
	{mso-style-name:"Definition List";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:18.0pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Times New Roman",serif;}
span.CODE
	{mso-style-name:CODE;
	font-family:"Courier New";}
p.Preformatted, li.Preformatted, div.Preformatted
	{mso-style-name:Preformatted;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Courier New";}
span.Max
	{mso-style-name:"Max\.";
	font-weight:bold;}
p.H4, li.H4, div.H4
	{mso-style-name:H4;
	margin-top:5.0pt;
	margin-right:0cm;
	margin-bottom:5.0pt;
	margin-left:0cm;
	page-break-after:avoid;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Times New Roman",serif;
	font-weight:bold;}
p.coltit, li.coltit, div.coltit
	{mso-style-name:coltit;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StempelGaramond RomanSC",serif;
	color:white;
	letter-spacing:.5pt;}
p.H2, li.H2, div.H2
	{mso-style-name:H2;
	margin-top:5.0pt;
	margin-right:0cm;
	margin-bottom:5.0pt;
	margin-left:0cm;
	page-break-after:avoid;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:18.0pt;
	font-family:"Times New Roman",serif;
	font-weight:bold;}
p.Address, li.Address, div.Address
	{mso-style-name:Address;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Times New Roman",serif;
	font-style:italic;}
p.abstand, li.abstand, div.abstand
	{mso-style-name:abstand;
	margin-top:6.0pt;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Times New Roman",serif;
	letter-spacing:1.5pt;}
p.Normale, li.Normale, div.Normale
	{mso-style-name:Normale;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;}
p.z-BottomofForm, li.z-BottomofForm, div.z-BottomofForm
	{mso-style-name:"z-Bottom of Form";
	margin:0cm;
	text-align:center;
	punctuation-wrap:simple;
	text-autospace:none;
	border:none;
	padding:0cm;
	font-size:8.0pt;
	font-family:"Arial",sans-serif;
	display:none;}
p.H3, li.H3, div.H3
	{mso-style-name:H3;
	margin-top:5.0pt;
	margin-right:0cm;
	margin-bottom:5.0pt;
	margin-left:0cm;
	page-break-after:avoid;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:14.0pt;
	font-family:"Times New Roman",serif;
	font-weight:bold;}
p.Kopf, li.Kopf, div.Kopf
	{mso-style-name:Kopf;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"Times New Roman",serif;}
p.Text, li.Text, div.Text
	{mso-style-name:Text;
	margin:0cm;
	text-align:justify;
	text-indent:21.25pt;
	line-height:12.8pt;
	background:white;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:9.5pt;
	font-family:"Times New Roman",serif;}
p.Formatvorlage, li.Formatvorlage, div.Formatvorlage
	{mso-style-name:Formatvorlage;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;}
span.Betonung
	{mso-style-name:Betonung;
	font-style:italic;}
span.Hervorhebung1
	{mso-style-name:Hervorhebung1;
	font-style:italic;}
span.CharacterStyle4
	{mso-style-name:"Character Style 4";
	font-family:"Bookman Old Style",serif;}
p.Style1, li.Style1, div.Style1
	{mso-style-name:"Style 1";
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;}
span.CharacterStyle3
	{mso-style-name:"Character Style 3";
	font-family:"Bookman Old Style",serif;}
span.CharacterStyle2
	{mso-style-name:"Character Style 2";
	font-family:"Bookman Old Style",serif;}
p.Style3, li.Style3, div.Style3
	{mso-style-name:"Style 3";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:14.4pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Times New Roman",serif;}
p.Corpodeltesto3, li.Corpodeltesto3, div.Corpodeltesto3
	{mso-style-name:"Corpo del testo 3";
	margin:0cm;
	text-align:justify;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:18.0pt;
	font-family:"Arial",sans-serif;}
p.Style6, li.Style6, div.Style6
	{mso-style-name:"Style 6";
	margin:0cm;
	line-height:117%;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Bookman Old Style",serif;}
p.Formatvorlage2, li.Formatvorlage2, div.Formatvorlage2
	{mso-style-name:Formatvorlage2;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:Ahorus;
	text-decoration:line-through;}
p.Formatvorlage1, li.Formatvorlage1, div.Formatvorlage1
	{mso-style-name:Formatvorlage1;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:Ahorus;}
p.Textkrper-Erstzeileneinzug1, li.Textkrper-Erstzeileneinzug1, div.Textkrper-Erstzeileneinzug1
	{mso-style-name:Textkörper-Erstzeileneinzug1;
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:6.0pt;
	margin-left:0cm;
	text-indent:10.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"StplGaramond",serif;}
p.Textkrper-Erstzeileneinzug21, li.Textkrper-Erstzeileneinzug21, div.Textkrper-Erstzeileneinzug21
	{mso-style-name:"Textkörper-Erstzeileneinzug 21";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:6.0pt;
	margin-left:14.15pt;
	text-indent:10.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"StplGaramond",serif;}
p.Default, li.Default, div.Default
	{mso-style-name:Default;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Times New Roman",serif;
	color:black;}
span.fliesstext
	{mso-style-name:fliesstext;}
p.Sprechblasentext1, li.Sprechblasentext1, div.Sprechblasentext1
	{mso-style-name:Sprechblasentext1;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.0pt;
	font-family:"Tahoma",sans-serif;}
p.Textkrper21, li.Textkrper21, div.Textkrper21
	{mso-style-name:"Textkörper 21";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:6.0pt;
	margin-left:14.15pt;
	text-align:justify;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;
	color:black;
	letter-spacing:.25pt;}
span.n0x958f808x0x9584608
	{mso-style-name:n0x958f808x0x9584608;}
span.ital
	{mso-style-name:ital;}
span.bold
	{mso-style-name:bold;}
p.Style19, li.Style19, div.Style19
	{mso-style-name:"Style 19";
	margin-top:0cm;
	margin-right:0cm;
	margin-bottom:0cm;
	margin-left:36.0pt;
	line-height:113%;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:9.0pt;
	font-family:"Times New Roman",serif;
	font-style:italic;}
p.Style5, li.Style5, div.Style5
	{mso-style-name:"Style 5";
	margin-top:0cm;
	margin-right:36.0pt;
	margin-bottom:0cm;
	margin-left:7.2pt;
	text-align:justify;
	text-indent:-7.2pt;
	line-height:125%;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.0pt;
	font-family:"Bookman Old Style",serif;}
p.Style2, li.Style2, div.Style2
	{mso-style-name:"Style 2";
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;}
span.StrongFettMLW
	{mso-style-name:"Strong\.FettMLW";
	font-weight:bold;}
span.lmlsenserectebase
	{mso-style-name:lmlsenserectebase;}
span.lmlsenseboldbase
	{mso-style-name:lmlsenseboldbase;}
span.Unterpungiert
	{mso-style-name:Unterpungiert;
	text-decoration:underline;}
span.StandardMLW
	{mso-style-name:StandardMLW;
	text-decoration:none;
	vertical-align:baseline;}
span.SprechblasentextZchn
	{mso-style-name:"Sprechblasentext Zchn";
	font-family:"Tahoma",sans-serif;
	color:black;}
p.Dokumentstruktur1, li.Dokumentstruktur1, div.Dokumentstruktur1
	{mso-style-name:Dokumentstruktur1;
	margin:0cm;
	text-align:justify;
	text-indent:6.5pt;
	line-height:-73%;
	background:navy;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Tahoma",sans-serif;
	color:black;}
p.NurText1, li.NurText1, div.NurText1
	{mso-style-name:"Nur Text1";
	margin:0cm;
	text-indent:6.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Courier New";}
span.berschrift1Zchn
	{mso-style-name:"Überschrift 1 Zchn";
	font-family:"StplGaramond",serif;
	color:black;
	font-weight:bold;}
span.berschrift2Zchn
	{mso-style-name:"Überschrift 2 Zchn";
	font-family:"StplGaramond",serif;
	color:black;
	font-weight:bold;}
span.berschrift3Zchn
	{mso-style-name:"Überschrift 3 Zchn";
	font-family:"StplGaramond",serif;
	color:black;
	font-weight:bold;}
span.berschrift4Zchn
	{mso-style-name:"Überschrift 4 Zchn";
	font-family:"StplGaramond",serif;
	color:black;
	font-weight:bold;}
span.berschrift5Zchn
	{mso-style-name:"Überschrift 5 Zchn";
	color:black;
	font-weight:bold;}
span.berschrift6Zchn
	{mso-style-name:"Überschrift 6 Zchn";
	color:black;
	text-decoration:underline;}
span.berschrift7Zchn
	{mso-style-name:"Überschrift 7 Zchn";
	color:black;
	font-style:italic;}
span.berschrift8Zchn
	{mso-style-name:"Überschrift 8 Zchn";
	color:black;
	font-style:italic;}
span.berschrift9Zchn
	{mso-style-name:"Überschrift 9 Zchn";
	color:black;
	font-style:italic;}
span.FuzeileZchn
	{mso-style-name:"Fußzeile Zchn";
	font-family:"StplGaramond",serif;
	color:black;}
span.KopfzeileZchn
	{mso-style-name:"Kopfzeile Zchn";
	font-family:"StplGaramond",serif;
	color:black;}
span.FunotentextZchn
	{mso-style-name:"Fußnotentext Zchn";
	font-family:"StplGaramond",serif;
	color:black;}
span.DokumentstrukturZchn
	{mso-style-name:"Dokumentstruktur Zchn";
	font-family:"Tahoma",sans-serif;
	color:black;}
p.NurText2, li.NurText2, div.NurText2
	{mso-style-name:"Nur Text2";
	margin:0cm;
	text-indent:6.5pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Courier New";}
span.Fett1
	{mso-style-name:Fett1;
	font-weight:bold;}
span.CharacterStyle1
	{mso-style-name:"Character Style 1";
	font-family:"Bookman Old Style",serif;}
span.expital
	{mso-style-name:"exp ital";}
p.Kommentarthema1, li.Kommentarthema1, div.Kommentarthema1
	{mso-style-name:Kommentarthema1;
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;
	font-weight:bold;}
p.PlainText1, li.PlainText1, div.PlainText1
	{mso-style-name:"Plain Text1";
	margin:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:10.0pt;
	font-family:"Times New Roman",serif;}
span.BesuchterLink1
	{mso-style-name:BesuchterLink1;
	color:olive;
	text-decoration:underline;}
span.KommentartextZchn
	{mso-style-name:"Kommentartext Zchn";
	font-family:"StplGaramond",serif;
	color:black;}
span.KommentarthemaZchn
	{mso-style-name:"Kommentarthema Zchn";
	font-family:"StplGaramond",serif;
	color:black;
	font-weight:bold;}
span.exp
	{mso-style-name:exp;}
p.StandardWeb1, li.StandardWeb1, div.StandardWeb1
	{mso-style-name:"Standard \(Web\)1";
	margin-top:5.0pt;
	margin-right:0cm;
	margin-bottom:5.0pt;
	margin-left:0cm;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:12.0pt;
	font-family:"Times New Roman",serif;}
span.excl
	{mso-style-name:excl;}
span.high
	{mso-style-name:high;}
span.defla
	{mso-style-name:def_la;}
span.st
	{mso-style-name:st;}
span.NurTextZchn
	{mso-style-name:"Nur Text Zchn";
	font-family:Consolas;}
span.mlwsenserectebase
	{mso-style-name:mlwsenserectebase;}
span.highlight
	{mso-style-name:highlight;}
span.mlwexpanrectebase
	{mso-style-name:mlwexpanrectebase;}
span.hyphfragment
	{mso-style-name:hyph_fragment;}
p.innegabilisinnegabilis, li.innegabilisinnegabilis, div.innegabilisinnegabilis
	{mso-style-name:innegabilisinnegabilis;
	margin:0cm;
	text-align:justify;
	text-indent:6.5pt;
	line-height:8.8pt;
	punctuation-wrap:simple;
	text-autospace:none;
	font-size:8.5pt;
	font-family:"StplGaramond",serif;}
span.mlwsenseitalicsbase
	{mso-style-name:mlwsenseitalicsbase;}
span.msoIns
	{mso-style-name:"";
	text-decoration:underline;
	color:teal;}
span.msoDel
	{mso-style-name:"";
	text-decoration:line-through;
	color:red;}
.MsoChpDefault
	{font-size:10.0pt;}
 /* Page Definitions */
 @page WordSection1
	{size:21.0cm 841.95pt;
	margin:4.0cm 53.0pt 95.0pt 54.0pt;}
div.WordSection1
	{page:WordSection1;}
 /* List Definitions */
 ol
	{margin-bottom:0cm;}
ul
	{margin-bottom:0cm;}
-->
</style>

</head>

<body lang=DE link=blue vlink="#954F72" style='word-wrap:break-word'>

<div class=WordSection1>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>k</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>littera</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>decima</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>alphabeti</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Latini.</span></i><span lang=EN-US>  </span><span
class=jofu2><span lang=EN-US style='font-size:8.0pt;font-family:"Arial",sans-serif;
color:#0070C0;letter-spacing:0pt'>Häberlin</span></span><span lang=EN-US>[MFSP] 
</span><b><span lang=EN-US>1</span></b><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>gener.</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Otfr.</span><span lang=EN-US> </span><span
lang=EN-US>ad</span><span lang=EN-US> </span><span lang=EN-US>Liutb.</span><span
lang=EN-US> </span><span lang=EN-US>70sqq.</span><span lang=EN-US> </span><span
lang=EN-US>k</span><span lang=EN-US> </span><span lang=EN-US>et</span><span
lang=EN-US> </span><span lang=EN-US>z</span><span lang=EN-US> </span><span
lang=EN-US>sepius</span><span lang=EN-US> </span><span lang=EN-US>haec</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>Theotisca)</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US>lingua</span><span
lang=EN-US> </span><span lang=EN-US>extra</span><span lang=EN-US> </span><span
lang=EN-US>usum</span><span lang=EN-US> </span><span lang=EN-US>Latinitatis</span><span
lang=EN-US> </span><span lang=EN-US>utitur</span><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US
style='letter-spacing:1.75pt'>.</span><span lang=EN-US>;</span><span
lang=EN-US> </span><span lang=EN-US>ob</span><span lang=EN-US> </span><span
lang=EN-US>stridorem</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>dentium</span><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>hac</span><span lang=EN-US> </span><span lang=EN-US>lingua</span><span
lang=EN-US> </span><span lang=EN-US>z</span><span lang=EN-US> </span><span
lang=EN-US>utuntur,</span><span lang=EN-US> </span><span lang=EN-US>k</span><span
lang=EN-US> </span><span lang=EN-US>autem</span><span lang=EN-US> </span><span
lang=EN-US>ob</span><span lang=EN-US> </span><span lang=EN-US>fautium</span><span
lang=EN-US> </span><span lang=EN-US>sonoritatem.</span><span lang=EN-US>[MFSP]</span><b><span
lang=EN-US>2</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>mus.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>de</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>littera</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>significativa</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>
</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>neumatibus</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>addita</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>(‘Romanusbuchstabe’;</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>de</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>re</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>LexMusLat.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>vol.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>II.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>s.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>v.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>‘k’)</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Notker.</span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Balb.</span><span lang=EN-US> </span><span lang=EN-US>ad</span><span
lang=EN-US> </span><span lang=EN-US>Lantb.</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>36,21</span><span
lang=EN-US> </span><span lang=EN-US>k</span><span lang=EN-US> </span><span
lang=EN-US>licet</span><span lang=EN-US> </span><span lang=EN-US>apud</span><span
lang=EN-US> </span><span lang=EN-US>Latinos</span><span lang=EN-US> </span><span
lang=EN-US>nihil</span><span lang=EN-US> </span><span lang=EN-US>valeat,</span><span
lang=EN-US> </span><span lang=EN-US>apud</span><span lang=EN-US> </span><span
lang=EN-US>nos</span><span lang=EN-US> </span><span lang=EN-US>tamen</span><span
lang=EN-US> </span><span lang=EN-US>Alemannos</span><span lang=EN-US> </span><span
lang=EN-US>pro</span><span lang=EN-US> </span><span lang=EN-US>x</span><span
lang=EN-US> </span><span lang=EN-US>(<i><span style='letter-spacing:.25pt'>i.</span></i></span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US
style='font-family:"OldGreekSerif Normal"'>x</span><span lang=EN-US>)</span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US>Greca</span><span
lang=EN-US> </span><span lang=EN-US>positum<span style='letter-spacing:-1.75pt'>:</span></span><span
lang=EN-US> </span><span lang=EN-US>chlenche</span><span lang=EN-US> </span><span
lang=EN-US>(klenche</span><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>sim.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>var.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>l.</span></i><span lang=EN-US>),</span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US>id</span><span
lang=EN-US> </span><span lang=EN-US>est</span><span lang=EN-US> </span><span
lang=EN-US>clange,</span><span lang=EN-US> </span><span lang=EN-US>clamitat</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(inde</span></i><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Frutolf.</span><span lang=EN-US> </span><span lang=EN-US>[?]</span><span
lang=EN-US> </span><span lang=EN-US>brev.</span><span lang=EN-US> </span><span
lang=EN-US>14</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>104.</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>al.).</span></i><span lang=EN-US>[MFSP]</span><b><span
lang=EN-US>3</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>math.</span></i><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>numerum</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>CL</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>significans</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Carm.</span><span
lang=EN-US> </span><span lang=EN-US>de</span><span lang=EN-US> </span><span
lang=EN-US>litt.</span><span lang=EN-US> </span>11 k centenarium medium servat et
unum.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kabrates</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cabrates.[VERWEIS]<span style='font-size:
6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kacabre</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>cacabre.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kaçia</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cacia.[VERWEIS]<b>kado</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cado.[VERWEIS]<b>kaganus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> caganus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kahtena</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>catena.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kaikias</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>caecias.</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>II.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>20,56sqq.</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Albert.</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span style='font-variant:small-caps;letter-spacing:
.5pt'>M.</span> meteor. 3,1,22 p. 123,46 ab oriente autem solstitiali aestivo apud
nos sine nomine est, quem Graeci tamen k‑<u><span style='display:none'>aiki</span></u>an
vocant.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>[kaiparios</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> ceparius.<b>]</b>[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kakabre</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>cacabre.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kakodaemon</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cacodaemon.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kakotheon</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cacotheon.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kalcecutium</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>chalcecutium.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kalendae</b>, ‑arum <i><span
style='letter-spacing:.25pt'>f.</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>pl.</span></i> (<i><span
style='letter-spacing:.25pt'>sg.</span><span style='letter-spacing:-1.75pt'>:</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>43</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span></i><i><span style='letter-spacing:-1.5pt'> </span><span
style='letter-spacing:.25pt'>p.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>2542</span><span style='letter-spacing:
-1.5pt'>,</span></i><i><span style='letter-spacing:-1.5pt'> </span><span
style='letter-spacing:.25pt'>18</span></i>. <i><span style='letter-spacing:
.25pt'>adde</span></i> <span style='font-variant:small-caps;letter-spacing:
.5pt'>Primord.</span> Windb. 3 p. 563,1).[MFSP]<i><span style='letter-spacing:
.25pt'>script.</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>et</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>form.</span><span style='letter-spacing:
-1.75pt'>:</span></i>[MFSP]ca-<span style='letter-spacing:-1.75pt'>:</span> <i><span style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>41</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>43</span><span style='letter-spacing:
-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'> </span></i><i><span
style='letter-spacing:-1.5pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>2542</span><span
style='letter-spacing:-1.5pt'>,</span></i><i><span style='letter-spacing:-1.5pt'>
</span><span style='letter-spacing:.25pt'>32</span></i>. <i><span
style='letter-spacing:.25pt'>al</span></i>.[MFSP]kall-<span style='letter-spacing:
-1.75pt'>:</span><i><span style='letter-spacing:.25pt'> </span></i><i><span style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>52</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>54</span></i>.[MFSP](ca-, ka)lan-<span
style='letter-spacing:-1.75pt'>:</span><i><span style='letter-spacing:.25pt'> </span></i><i><span style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>28</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>47</span><span style='letter-spacing:
-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'> </span><span
style='letter-spacing:.25pt'>49</span></i>. <i><span style='letter-spacing:
.25pt'>al.</span></i>[MFSP]<i><span style='letter-spacing:.25pt'>masc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>decl.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>II.</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><i><span style='letter-spacing:.25pt'>l</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>30</span><span style='letter-spacing:
-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'> </span><span
style='letter-spacing:.25pt'>51</span></i>.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>I</b> <i><span
style='letter-spacing:.25pt'>proprie</span><span style='letter-spacing:-1.75pt'>:</span></i>[MFSP]<b>A</b>
<i><span style='letter-spacing:.25pt'>strictius</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>i.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dies</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>primus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>initium</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>erster</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Tag</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>des</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Monats,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Monatsanfang,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‘Kalenden’</span><span
style='letter-spacing:-1.75pt'>:</span></i>[MFSP]<b>1</b> <i><span
style='letter-spacing:.25pt'>in</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>univ.</span><span style='letter-spacing:
-1.75pt'>:</span></i> <span style='font-variant:small-caps;letter-spacing:.5pt'>Sermo</span>
de sacril. <span lang=EN-US>23</span><span lang=EN-US> </span><span lang=EN-US>dies</span><span
lang=EN-US> </span><span lang=EN-US>c<a name="kalendae5m_1"></a>alandarum,</span><span
lang=EN-US> </span><span lang=EN-US>quas</span><span lang=EN-US> </span><span
lang=EN-US>Ianuarias</span><span lang=EN-US> </span><span lang=EN-US>vocant,</span><span
lang=EN-US> </span><span lang=EN-US>a</span><span lang=EN-US> </span><span
lang=EN-US>Iano,</span><span lang=EN-US> </span><span lang=EN-US>homine</span><span
lang=EN-US> </span><span lang=EN-US>perdito,</span><span lang=EN-US> </span><span
lang=EN-US>nomen</span><span lang=EN-US> </span><span lang=EN-US>accipit.</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Comput.</span><span lang=EN-US> </span><span lang=EN-US>Borst.</span><span
lang=EN-US> </span><span lang=EN-US>2,7</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalend</span></u>e</span><span
lang=EN-US> </span><span lang=EN-US>(‑<u><span style='display:none'>kalend</span></u>i</span><a
name="kalendae2m_1"></a><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>var.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>l.</span></i><span lang=EN-US>)</span><span lang=EN-US> </span><span
lang=EN-US>interpretantur</span><span lang=EN-US> </span><span lang=EN-US>exordia</span><span
lang=EN-US> </span><span lang=EN-US>mensium,</span><span lang=EN-US> </span><span
lang=EN-US>sed</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalend</span></u>as</span><span lang=EN-US> </span><span
lang=EN-US>a</span><span lang=EN-US> </span><span lang=EN-US>colendo</span><span
lang=EN-US> </span><span lang=EN-US>dictis</span><span lang=EN-US> </span><span
lang=EN-US>dicitur.</span><span lang=EN-US> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Liutolf.</span><span
lang=EN-US> </span><span lang=EN-US>Sever.</span><span lang=EN-US> </span><span
lang=EN-US>I</span><span lang=EN-US> </span><span lang=EN-US>5</span><span
lang=EN-US> </span><span lang=EN-US>interrogavi</span><span lang=EN-US> </span><span
lang=EN-US>de</span><span lang=EN-US> </span><span lang=EN-US>festivitatibus</span><span
lang=EN-US> </span><span lang=EN-US>sanctorum,</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>quotis</span><span
lang=EN-US> </span><span lang=EN-US>essent</span><span lang=EN-US> </span><span
lang=EN-US>celebrandae</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalend</span></u>is</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>eqs.</span></i><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Capit.</span><span
lang=EN-US> </span><span lang=EN-US>episc.</span><span lang=EN-US> </span><span
lang=EN-US>I</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>65,19</span><span lang=EN-US> </span><span
lang=EN-US>iubemus,</span><span lang=EN-US> </span><span lang=EN-US>ut</span><span
lang=EN-US> </span><span lang=EN-US>omnibus</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalend</span></u>is</span><span
lang=EN-US> </span><span lang=EN-US>archipresbyteri</span><span lang=EN-US> </span><span
lang=EN-US>nostri</span><span lang=EN-US> </span><span lang=EN-US>suos</span><span
lang=EN-US> </span><span lang=EN-US>consacerdotes</span><span lang=EN-US> </span><span
lang=EN-US>ad</span><span lang=EN-US> </span><span lang=EN-US>concilium</span><span
lang=EN-US> </span><span lang=EN-US>evocent</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>eqs</span></i><span lang=EN-US>.</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>saepe.</span></i><span
lang=EN-US>[MFSP]</span><b><span lang=EN-US>2</span></b><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>in</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>designatione</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>
</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>certi</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>diei</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>(fere</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>forma</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>abbreviata;</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>cf.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>H.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Grotefend,</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>Abriss</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>der</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Chronologie</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>des</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>dt.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>Mittelalters</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>und</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>der</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Neuzeit.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span style='font-size:7.0pt;
position:relative;top:-2.0pt;letter-spacing:.25pt'>2</span><span
style='letter-spacing:.25pt'>1912.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>32sqq.)</span><span
style='letter-spacing:-1.75pt'>:</span></i>[MFSP]<b>a</b> <i><span
style='letter-spacing:.25pt'>spectat</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>ad</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>primum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>diem</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis</span><span
style='letter-spacing:-1.75pt'>:</span></i><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span style='font-variant:small-caps;letter-spacing:
.5pt'>Trad.</span> Patav. <span lang=EN-US>2</span><span lang=EN-US> </span><span
lang=EN-US>(a.</span><span lang=EN-US> </span><span lang=EN-US>739)</span><span
lang=EN-US> </span><span lang=EN-US>qui</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(episcopus)</span></i><span lang=EN-US>
</span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>consecravit</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>ecclesiam)</span></i><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>nomine</span><span
lang=EN-US> </span><span lang=EN-US>sanctae</span><span lang=EN-US> </span><span
lang=EN-US>Mariae</span><span lang=EN-US> </span><span lang=EN-US>et</span><span
lang=EN-US> </span><span lang=EN-US>constituit</span><span lang=EN-US> </span><span
lang=EN-US>diem</span><span lang=EN-US> </span><span lang=EN-US>sollemnem</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>kal.</span><span lang=EN-US> </span><span lang=EN-US>Novembris.</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Calend.</span><span lang=EN-US> </span><span lang=EN-US>Karol.</span><span
lang=EN-US> </span><span lang=EN-US>B</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>420,7</span><span
lang=EN-US> </span><span lang=EN-US>mense</span><span lang=EN-US> </span><span
lang=EN-US>Ianuario</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>c‑<u><span style='display:none'>alend</span></u>i<a
name="kalendae3m_1"></a>s</span><span lang=EN-US> </span><span lang=EN-US>nox</span><span
lang=EN-US> </span><span lang=EN-US>habet</span><span lang=EN-US> </span><span
lang=EN-US>horas</span><span lang=EN-US> </span><span lang=EN-US>octodecim,</span><span
lang=EN-US> </span><span lang=EN-US>dies</span><span lang=EN-US> </span><span
lang=EN-US>habet</span><span lang=EN-US> </span><span lang=EN-US>horas</span><span
lang=EN-US> </span><span lang=EN-US>sex</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(v.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>notam</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>ed.)</span></i><span lang=EN-US>.</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Consuet.</span><span
lang=EN-US> </span><span lang=EN-US>Vird.</span><span lang=EN-US> </span><span
lang=EN-US>28</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>415,5</span><span lang=EN-US> </span><span
lang=EN-US>a</span><span lang=EN-US> </span><span lang=EN-US>supra</span><span
lang=EN-US> </span><span lang=EN-US>dicta</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Novembris)</span></i><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>c<a name="kalendae3m_2"></a>‑<u><span
style='display:none'>alend</span></u>a</span><a name="kalendae1m_1"></a><span
lang=EN-US> </span><span lang=EN-US>usque</span><span lang=EN-US> </span><span
lang=EN-US>ad</span><span lang=EN-US> </span><span lang=EN-US>Dominicam</span><span
lang=EN-US> </span><span lang=EN-US>Coenam</span><span lang=EN-US> </span><span
lang=EN-US>ad</span><span lang=EN-US> </span><span lang=EN-US>mandatum</span><span
lang=EN-US> </span><span lang=EN-US>fratres</span><span lang=EN-US> </span><span
lang=EN-US>habebunt</span><span lang=EN-US> </span><span lang=EN-US>calidam</span><span
lang=EN-US> </span><span lang=EN-US>aquam.</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>persaepe.</span></i><span lang=EN-US>[MFSP]</span><b><span
lang=EN-US>b</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>spectat</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>aliquos</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>dies</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>subtractos</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>a</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>die</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>primo</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>mensis</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>consequentis</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Chart.</span><span lang=EN-US> </span><span
lang=EN-US>Sangall.</span><span lang=EN-US> </span><span lang=EN-US>A</span><span
lang=EN-US> </span><span lang=EN-US>9</span><span lang=EN-US> </span><span
lang=EN-US>(a.</span><span lang=EN-US> </span><span lang=EN-US>744)</span><span
lang=EN-US> </span><span lang=EN-US>facta</span><span lang=EN-US> </span><span
lang=EN-US>cartola</span><span lang=EN-US> </span><span lang=EN-US>donationis</span><span
lang=EN-US> </span><span lang=EN-US>anno</span><span lang=EN-US> </span><span
lang=EN-US>XXX</span><span lang=EN-US> </span><span lang=EN-US>pos</span><span
lang=EN-US> </span><span lang=EN-US>regnu</span><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span>Dagopirti reies,<span style='letter-spacing:-.2pt'> </span>die<span
style='letter-spacing:-.2pt'> </span>tertium<span style='letter-spacing:-.2pt'>
</span>c<a name="kalendae5m_2"></a>alandas<span style='letter-spacing:-.2pt'> </span>Settenbris.<i><span
style='letter-spacing:.25pt'> </span></i><span style='font-variant:small-caps;
letter-spacing:.5pt'>Trad.</span> Ratisb. <span lang=EN-US>136</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>110,21</span><span lang=EN-US> </span><span lang=EN-US>actum</span><span
lang=EN-US> </span><span lang=EN-US>est</span><span lang=EN-US> </span><span
lang=EN-US>anno</span><span lang=EN-US> </span><span lang=EN-US>Arnulfi</span><span
lang=EN-US> </span><span lang=EN-US>regis</span><span lang=EN-US> </span><span
lang=EN-US>secundo</span><span lang=EN-US> </span><span lang=EN-US>VII.</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kalend</span></u>arum</span><span
lang=EN-US> </span><span lang=EN-US>(<i><span style='letter-spacing:.25pt'>corr.</span></i></span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>ed.</span></i><span lang=EN-US> </span>‑<u><span
style='display:none'>kal</span></u>a<a name="kalendae5m_3"></a>ndarum) Martialium.
<span style='font-variant:small-caps;letter-spacing:.5pt'>Chron.</span> Thietm.
<span lang=EN-US>7,63</span><span lang=EN-US> </span><span lang=EN-US>Heinricus</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>longa</span><span
lang=EN-US> </span><span lang=EN-US>egritudine</span><span lang=EN-US> </span><span
lang=EN-US>vexatus</span><span lang=EN-US> </span><span lang=EN-US>quartodecimo</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kalend</span></u>o<a
name="kalendae2m_2"></a>s</span><span lang=EN-US> </span><span lang=EN-US>Octobris</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>obiit.</span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Chart.</span><span
lang=EN-US> </span><span lang=EN-US>Bund.</span><span lang=EN-US> </span><span
lang=EN-US>903</span><span lang=EN-US> </span><span lang=EN-US>(epist.</span><span
lang=EN-US> </span><span lang=EN-US>papae)</span><span lang=EN-US> </span><span
lang=EN-US>dat.</span><span lang=EN-US> </span>Lugdunum, secundo kal<a
name="kalendae4m_1"></a>l. Marzii, pontificatus nostri anno vero octavo. <span
style='font-variant:small-caps;letter-spacing:.5pt'>Chart.</span> Ticin. 39 p. 123,28
<span style='font-variant:small-caps;letter-spacing:.5pt'>mcclxvii</span>, die Veneris,
<span style='font-variant:small-caps;letter-spacing:.5pt'>iiii</span><span
style='font-size:7.0pt;position:relative;top:-2.0pt'>o</span> ante k<a
name="kalendae4m_2"></a>all‑<u><span style='display:none'>end</span></u>as Martii
in burgo Lugani, in pallatio ecclesie episcopalis Cumane. <i><span
style='letter-spacing:.25pt'>persaepe.</span></i>[MFSP]<b>B</b> <i><span
style='letter-spacing:.25pt'>latius</span><span style='letter-spacing:-1.75pt'>:</span></i>[MFSP]<b>1</b>
<i><span style='letter-spacing:.25pt'>d<a name="kalendae8m_1"></a>ies</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>qui</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>a</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>die</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>primo</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>enumeratur,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>determinatur</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>nach</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dem</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Monatsersten,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>den</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kalenden</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>gezählter,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>bestimmter</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Tag</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>des</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Monats</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>A.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Borst,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Der</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>karoling.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Reichskalender.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>I.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>2001.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>60)</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Carm.</span> de temp. rat. 180 Mars et Maius, Mavors, Iulius,
October senis nonis moderantur, denas septenas dabunt ‑<u><span
style='display:none'>kalend</span></u>as. <span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Carm.</span><span lang=EN-US> </span><span
lang=EN-US>de</span><span lang=EN-US> </span><span lang=EN-US>conc.</span><span
lang=EN-US> </span><span lang=EN-US>mens.</span><span lang=EN-US> </span><span
lang=EN-US>1,2</span><span lang=EN-US> </span><span lang=EN-US>Ianuarius,</span><span
lang=EN-US> </span><span lang=EN-US>December</span><span lang=EN-US> </span><span
lang=EN-US>et</span><span lang=EN-US> </span><span lang=EN-US>Augustus</span><span
lang=EN-US> </span><span lang=EN-US>pariter</span><span lang=EN-US> </span><span
lang=EN-US>quarto</span><span lang=EN-US> </span><span lang=EN-US>nonas</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalend</span></u>as</span><span
lang=EN-US> </span><span lang=EN-US>habent</span><span lang=EN-US> </span><span
lang=EN-US>nono</span><span lang=EN-US> </span><span lang=EN-US>decimo.</span><span
lang=EN-US> </span><span lang=EN-US>2,2</span><span lang=EN-US> </span><span
lang=EN-US>Martius</span><span lang=EN-US> </span><span lang=EN-US>cum</span><span
lang=EN-US> </span><span lang=EN-US>Maio,</span><span lang=EN-US> </span><span
lang=EN-US>cum</span><span lang=EN-US> </span><span lang=EN-US>Octimbre</span><span
lang=EN-US> </span><span lang=EN-US>Iulius</span><span lang=EN-US> </span><span
lang=EN-US>sexto</span><span lang=EN-US> </span><span lang=EN-US>nonas</span><span
lang=EN-US> </span><span lang=EN-US>dant</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalend</span></u>as</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>septimo</span><span lang=EN-US> </span><span lang=EN-US>decimo.</span><span
lang=EN-US> </span><span lang=EN-US>3,3</span><span lang=EN-US> </span><span
lang=EN-US>Aprilis</span><span lang=EN-US> </span><span lang=EN-US>et</span><span
lang=EN-US> </span><span lang=EN-US>November,</span><span lang=EN-US> </span><span
lang=EN-US>September</span><span lang=EN-US> </span><span lang=EN-US>et</span><span
lang=EN-US> </span><span lang=EN-US>Iunius</span><span lang=EN-US> </span><span
lang=EN-US>quarto</span><span lang=EN-US> </span><span lang=EN-US>nonas</span><span
lang=EN-US> </span><span lang=EN-US>simul</span><span lang=EN-US> </span><span
lang=EN-US>gestant</span><span lang=EN-US> </span><span lang=EN-US>et</span><span
lang=EN-US> </span><span lang=EN-US>octavo</span><span lang=EN-US> </span><span
lang=EN-US>decimo</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalend</span></u>arum.</span><span lang=EN-US>[MFSP]</span><b><span
lang=EN-US>2</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>de</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>certo</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>die</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>mensis</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>i.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>q.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>dies</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>–</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Tag</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Agius</span><span
lang=EN-US> </span><span lang=EN-US>comput.</span><span lang=EN-US> </span><span
lang=EN-US>2,10</span><span lang=EN-US> </span><span lang=EN-US>apposui</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>numerum,</span><span
lang=EN-US> </span><span lang=EN-US>quo</span><span lang=EN-US> </span><span
lang=EN-US>quasque</span><span lang=EN-US> </span><span lang=EN-US>solemus</span><span
lang=EN-US> </span><span lang=EN-US>una</span><span lang=EN-US> </span><span
lang=EN-US>cum</span><span lang=EN-US> </span><span lang=EN-US>feriis</span><span
lang=EN-US> </span><span lang=EN-US>investigare</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalend</span></u>as.</span><span
lang=EN-US> </span><span lang=EN-US>6,17</span><span lang=EN-US> </span><span
lang=EN-US>ipse</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalend</span></u>arum</span><span lang=EN-US> </span><span
lang=EN-US>numerus</span><span lang=EN-US> </span><span lang=EN-US>hic</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>in</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>pagina</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>sexta)</span></i><span lang=EN-US> </span><span
lang=EN-US>subditus</span><span lang=EN-US> </span><span lang=EN-US>una</span><span
lang=EN-US> </span><span lang=EN-US>praesentis</span><span lang=EN-US> </span><span
lang=EN-US>iunctus</span><span lang=EN-US> </span><span lang=EN-US>cum</span><span
lang=EN-US> </span><span lang=EN-US>concurrentibus</span><span lang=EN-US> </span><span
lang=EN-US>anni.</span><span lang=EN-US> </span><span lang=EN-US>8,17</span><span
lang=EN-US> </span><span lang=EN-US>si</span><span lang=EN-US> </span><span
lang=EN-US>nosse</span><span lang=EN-US> </span><span lang=EN-US>cupis,</span><span
lang=EN-US> </span><span lang=EN-US>quis</span><span lang=EN-US> </span><span
lang=EN-US>pascha</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalend</span></u>is,</span><span lang=EN-US> </span><span
lang=EN-US>quis</span><span lang=EN-US> </span><span lang=EN-US>quoque</span><span
lang=EN-US> </span><span lang=EN-US>festa</span><span lang=EN-US> </span><span
lang=EN-US>cluant.</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>ibid.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>al.</span></i><span lang=EN-US>[MFSP]</span><b><span lang=EN-US>3</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>de</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>spatio</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>a</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>die</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>primo</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>mensis</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>usque</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>ad</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>diem</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>primum</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>mensis</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>consequentis</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>i.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>q.</span></i><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>mensis</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>–</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>Monat</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Lex</span><span
lang=EN-US> </span><span lang=EN-US>Baiuv.</span><span lang=EN-US> </span><span
lang=EN-US>2,14</span><span lang=EN-US> </span><span lang=EN-US>ut</span><span
lang=EN-US> </span><span lang=EN-US>placita</span><span lang=EN-US> </span><span
lang=EN-US>fiant</span><span lang=EN-US> </span><span lang=EN-US>per</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kalend</span></u>as</span><span
lang=EN-US> </span><span lang=EN-US>aut</span><span lang=EN-US> </span><span
lang=EN-US>post</span><span lang=EN-US> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>xv</span><span lang=EN-US> </span><span
lang=EN-US>dies,</span><span lang=EN-US> </span><span lang=EN-US>si</span><span
lang=EN-US> </span><span lang=EN-US>necesse</span><span lang=EN-US> </span><span
lang=EN-US>est,</span><span lang=EN-US> </span><span lang=EN-US>ad</span><span
lang=EN-US> </span><span lang=EN-US>causas</span><span lang=EN-US> </span><span
lang=EN-US>inquirendas</span><span lang=EN-US> </span><span lang=EN-US>(<i><span
style='letter-spacing:.25pt'>sim.</span></i></span><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Const.</span><span lang=EN-US> </span><span
lang=EN-US>Melf.</span><span lang=EN-US> </span><span lang=EN-US>1,52,1).</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Form.</span><span lang=EN-US> </span><span lang=EN-US>Augiens.</span><span
lang=EN-US> </span><span lang=EN-US>C</span><span lang=EN-US> </span><span
lang=EN-US>3</span><span lang=EN-US> </span><span lang=EN-US>littere</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>prudencie</span><span
lang=EN-US> </span><span lang=EN-US>vestrae</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>illo</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>die)</span></i><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalend</span></u>e</span><a
name="kalendae1m_2"></a><span lang=EN-US> </span><span lang=EN-US>per</span><span
lang=EN-US> </span><span lang=EN-US>horam</span><span lang=EN-US> </span><span
lang=EN-US>nonam</span><span lang=EN-US> </span><span lang=EN-US>diei</span><span
lang=EN-US> </span><span lang=EN-US>ad</span><span lang=EN-US> </span><span
lang=EN-US>me</span><span lang=EN-US> </span><span lang=EN-US>pervenerunt,</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>senior</span><span lang=EN-US> </span><span lang=EN-US>meus</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>ill.</span><span lang=EN-US> </span><span lang=EN-US>kal.</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>iter</span><span
lang=EN-US> </span><span lang=EN-US>arripiebat.</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Rather.</span><span
lang=EN-US> </span><span lang=EN-US>epist.</span><span lang=EN-US> </span><span
lang=EN-US>25</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>126,2</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>quibus</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kalend</span></u>is,</span><span
lang=EN-US> </span><span lang=EN-US>non</span><span lang=EN-US> </span><span
lang=EN-US>cures,</span><span lang=EN-US> </span><span lang=EN-US>de</span><span
lang=EN-US> </span><span lang=EN-US>die</span><span lang=EN-US> </span><span
lang=EN-US>solummodo</span><span lang=EN-US> </span><span lang=EN-US>cogita</span><span
lang=EN-US> </span><span lang=EN-US>(<i><span style='letter-spacing:.25pt'>sim.</span></i></span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>126,8).</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Vita</span><span
lang=EN-US> </span><span lang=EN-US>Anselmi</span><span lang=EN-US> </span><span
lang=EN-US>Non.</span><span lang=EN-US> </span><span lang=EN-US>5</span><span
lang=EN-US> </span><span lang=EN-US>(MGLang.</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>568,40)</span><span
lang=EN-US> </span><span lang=EN-US>ex</span><span lang=EN-US> </span><span
lang=EN-US>illius</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>beneficio</span><span lang=EN-US> </span><span
lang=EN-US>pauperes</span><span lang=EN-US> </span><span lang=EN-US>duocentos</span><span
lang=EN-US> </span><span lang=EN-US>per</span><span lang=EN-US> </span><span
lang=EN-US>omnes</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalend</span></u>as</span><span lang=EN-US> </span><span
lang=EN-US>pascebantur</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>(v.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>notam</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>ed.)</span></i><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Carm.</span><span lang=EN-US> </span><span lang=EN-US>Bur.</span><span
lang=EN-US> </span><span lang=EN-US>131</span><span lang=EN-US
style='font-size:7.0pt;position:relative;top:-2.0pt'>a</span><span lang=EN-US>,2,8</span><span
lang=EN-US> </span><span lang=EN-US>frustra</span><span lang=EN-US> </span><span
lang=EN-US>tuis</span><span lang=EN-US> </span><span lang=EN-US>litteris</span><span
lang=EN-US> </span><span lang=EN-US>inniteris;</span><span lang=EN-US> </span><span
lang=EN-US>moraberis</span><span lang=EN-US> </span><span lang=EN-US>per</span><span
lang=EN-US> </span><span lang=EN-US>plurimas</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalend</span></u>as.</span><span
lang=EN-US>[MFSP]</span><i><span lang=EN-US style='letter-spacing:.25pt'>fort.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>huc</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>spectat</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Carm.</span><span lang=EN-US> </span><span lang=EN-US>var.</span><span
lang=EN-US> </span>III 27,2,41,15 qui post me maneas, venientes adde ‑<u><span
style='display:none'>kalend</span></u>as, prosa metrique pedes tunc mihi consimiles.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>II</b> <i><span
style='letter-spacing:.25pt'>meton.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>de</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>festivitatibus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>vel</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>congregationibus,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>quae</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ex</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>consuetudine</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>die</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>primo</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>habebantur</span><span
style='letter-spacing:-1.75pt'>:</span></i>[MFSP]<b>A</b> <i><span
style='letter-spacing:.25pt'>de</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>festivitate</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ex</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ritibus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>paganis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>oriunda</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>i.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>festum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>anni</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>diei</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>primi</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Neujahrsfest,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‑feier</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>H.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Bächtold-Stäubli,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Handwb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>d.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dt.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Aberglaubens.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>VI.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>1934/35.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>p.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>1020sq.;</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>RAC</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>XXV.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>p.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>878sqq.)</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Epist.</span><span
lang=EN-US> </span><span lang=EN-US>Bonif.</span><span lang=EN-US> </span><span
lang=EN-US>51</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>90,20</span><span lang=EN-US> </span><span
lang=EN-US>de</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalend</span></u>is</span><span lang=EN-US> </span><span
lang=EN-US>(c<a name="kalendae3m_3"></a>‑<u><span style='display:none'>kalend</span></u>is</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>var.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>l.</span></i><span lang=EN-US>)</span><span
lang=EN-US> </span><span style='letter-spacing:2.25pt'>..</span>. Ianuariis vel
ceteris auguriis, filacteriis et incantationibus <span style='letter-spacing:
2.25pt'>..</span>. haec et nobis et omnibus christianis detestabile et pernitiosum
esse iudicamus dicente Deo<span style='letter-spacing:-1.75pt'>:</span> <i><span
style='letter-spacing:.25pt'>eqs.</span></i> (<i><span style='letter-spacing:
.25pt'>cf.</span></i> <span style='font-variant:small-caps;letter-spacing:.5pt'>Sermo</span>
de sacril. 17).[MFSP]<b>B</b> <i><span style='letter-spacing:.25pt'>conventus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(initio</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>habitus)</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Versammlung</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(am</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Monatsanfang)</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Fund.</span> Mur. 4 p. 12,25 ille <i><span
style='letter-spacing:.25pt'>(sc.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>presbyter</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Türing)</span></i>
numquam ausus est clericos in locum inducere vel ‑<u><span style='display:none'>kalend</span></u>as
illorum observare.[MFSP]<b>C</b> <i><span style='letter-spacing:.7pt'>?</span><span
style='letter-spacing:.25pt'>tributum</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>canonicis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>initio</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>solvendum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.7pt'>?</span><span
style='letter-spacing:.25pt'>am</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>Monatsanfang</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>zu</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>entrichtende</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Abgabe</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>an</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>die</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kanoniker</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Chart.</span> episc. Halb. 1161 l. 12 (a. 1267) bona <span
style='letter-spacing:2.25pt'>..</span>. portenario <span style='letter-spacing:
2.25pt'>..</span>. dedimus <i><span style='letter-spacing:.25pt'>(sc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>episcopus)</span></i>
in restaurum, scilicet <span style='letter-spacing:2.25pt'>..</span>. officium ‑<u><span
style='display:none'>kalend</span></u>arum in Dhingelstide, fertonem et dimidium
in Drubeke <i><span style='letter-spacing:.25pt'>eqs.</span></i><i><span
style='letter-spacing:.25pt'> </span></i>(<i><span style='letter-spacing:.25pt'>sim.</span></i>
1247 l. 14). <span style='font-variant:small-caps;letter-spacing:.5pt'>Chart.</span>
Francof. 368 quod die, quo computacio facta fuerit, dent <i><span
style='letter-spacing:.25pt'>(sc.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>camerarii)</span></i><i><span
style='letter-spacing:.25pt'> </span></i>nobis <i><span style='letter-spacing:
.25pt'>(sc.</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>canonicis)</span></i> ‑<u><span style='display:
none'>kalend</span></u>as nostras die eodem <i><span style='letter-spacing:
.25pt'>eqs</span></i>.[MFSP]<b>D</b> <i><span style='letter-spacing:.25pt'>iunctura</span></i><i><span
style='letter-spacing:.25pt'> </span></i>fratres ‑<u><span style='display:none'>kalend</span></u>arum
<i><span style='letter-spacing:.25pt'>i.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>collegium</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>fratrum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>calendariorum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>d.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>sog.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‘Kalandsbruderschaft’</span></i>
<i><span style='letter-spacing:.25pt'>(de</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>re</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>L<a
name="kalendae10m_1"></a>ThK.</span></i><i><span style='letter-spacing:.25pt'> </span></i><span
style='font-size:7.0pt;position:relative;top:-3.0pt'>3</span><i><span
style='letter-spacing:.25pt'>V.</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>1140;</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>cf.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span
style='letter-spacing:-1.5pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>2543</span><span
style='letter-spacing:-1.5pt'>,</span></i><i><span style='letter-spacing:-1.5pt'>
</span><span style='letter-spacing:.25pt'>60sqq.)</span><span style='letter-spacing:
-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'> </span></i><span
style='font-variant:small-caps;letter-spacing:.5pt'>Chart.</span> Westph. IV 233
(a. 1234) mansum <span style='letter-spacing:2.25pt'>..</span>. Heimanno plebano
contulimus <i><span style='letter-spacing:.25pt'>(sc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>fratres)</span></i>
<span style='letter-spacing:2.25pt'>..</span>. dantes ei plenam libertatem conferendi
eundem mansum fratribus ‑<u><span style='display:none'>kalend</span></u>arum sive,
cuicunque <span style='letter-spacing:2.25pt'>..</span>. decreverit conferendum.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>[kalendaricum</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>kalendatium.<b>]</b></p>

<p class=MsoNormal style='text-indent:6.5pt'><span class=lemma>kalendaris</span><b>,</b>
‑e.[MFSP]<i><span style='letter-spacing:.25pt'>ad</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kalendas</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>pertinens</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>auf</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>die</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kalenden</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>bezogen</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Bernold.</span><span
style='font-variant:small-caps;letter-spacing:.5pt'> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Const.</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US>chron.</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>393,35</span><span lang=EN-US> </span><span
lang=EN-US>(ed.</span><span lang=EN-US> </span><span lang=EN-US>Pertz)</span><span
lang=EN-US> </span><span lang=EN-US>utrique</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Romani</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>et</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Aegyptii)</span></i><span lang=EN-US> </span><span lang=EN-US>primi</span><span
lang=EN-US> </span><span lang=EN-US>sui</span><span lang=EN-US> </span><span
lang=EN-US>anni</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalendar</span></u>e<a name="kalendae9m_1"></a>s</span><span
lang=EN-US> </span><span lang=EN-US>lunae</span><span lang=EN-US> </span><span
lang=EN-US>aetates</span><span lang=EN-US> </span><span lang=EN-US>pro</span><span
lang=EN-US> </span><span lang=EN-US>regularibus</span><span lang=EN-US> </span><span
lang=EN-US>instituentes,</span><span lang=EN-US> </span><span lang=EN-US>ut</span><span
lang=EN-US> </span><span lang=EN-US>praescriptum</span><span lang=EN-US> </span><span
lang=EN-US>est,</span><span lang=EN-US> </span><span lang=EN-US>ordinaverunt</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(item</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>394,4;</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>cf.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>l</span></i><i><span lang=EN-US
style='letter-spacing:-.75pt'>.</span></i><i><span lang=EN-US style='letter-spacing:
-1.75pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>49)</span></i><span
lang=EN-US>.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><i><span style='letter-spacing:
.25pt'>adv.</span></i> <span style='font-size:6.0pt;font-family:Wingdings;
position:relative;top:-2.0pt'></span><b>kalendariter.</b>[MFSP]<i><span
style='letter-spacing:.25pt'>secundum</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>kalendarium</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>nach</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dem</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(Fest-,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kirchen‑)Kalender,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kalendarisch</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Conr.</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span style='font-variant:small-caps;letter-spacing:
.5pt'>Mur.</span> lib. ordin. <span lang=EN-US>749</span><span lang=EN-US> </span><span
lang=EN-US>sanctorum</span><span lang=EN-US> </span><span lang=EN-US>memoria</span><span
lang=EN-US> </span><span lang=EN-US>seu</span><span lang=EN-US> </span><span
lang=EN-US>celebritas</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>succedit</span><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>feriam</span><span lang=EN-US> </span><span lang=EN-US>ordinis</span><span
lang=EN-US> </span><span lang=EN-US>sanctorum,</span><span lang=EN-US> </span><span
lang=EN-US>propter</span><span lang=EN-US> </span><span lang=EN-US>quorum</span><span
lang=EN-US> </span><span lang=EN-US>festum</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalendarite</span></u>r</span><span
lang=EN-US> </span><span lang=EN-US>incidens</span><span lang=EN-US> </span><span
lang=EN-US>ipsa</span><span lang=EN-US> </span><span lang=EN-US>memoria</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>sua</span><span lang=EN-US> </span><span lang=EN-US>feria</span><span
lang=EN-US> </span><span lang=EN-US>non</span><span lang=EN-US> </span><span
lang=EN-US>fuerat</span><span lang=EN-US> </span><span lang=EN-US>celebrata.</span><span
lang=EN-US> </span><span lang=EN-US>1132</span><span lang=EN-US> </span><span
lang=EN-US>quod</span><span lang=EN-US> </span><span lang=EN-US>celebritas</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>propter</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>festorum</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>translationem</span><span
lang=EN-US> </span><span lang=EN-US>a</span><span lang=EN-US> </span><span
lang=EN-US>sua</span><span lang=EN-US> </span><span lang=EN-US>feriali</span><span
lang=EN-US> </span><span lang=EN-US>littera,</span><span lang=EN-US> </span><span
lang=EN-US>cui</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalendarite</span></u>r</span><span lang=EN-US> </span><span
lang=EN-US>est</span><span lang=EN-US> </span><span lang=EN-US>asscriptum,</span><span
lang=EN-US> </span><span lang=EN-US>nullatenus</span><span lang=EN-US> </span><span
lang=EN-US>moveatur.</span><span lang=EN-US> </span><span lang=EN-US>1285</span><span
lang=EN-US> </span><span lang=EN-US>mencio</span><span lang=EN-US> </span><span
lang=EN-US>de</span><span lang=EN-US> </span><span lang=EN-US>septem</span><span
lang=EN-US> </span><span lang=EN-US>Machabeis</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>loco</span><span
lang=EN-US> </span><span lang=EN-US>sibi</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalendarite</span></u>r</span><span
lang=EN-US> </span><span lang=EN-US>ascripto</span><span lang=EN-US> </span><span
lang=EN-US>habeatur</span><span lang=EN-US> </span><span lang=EN-US>(<i><span
style='letter-spacing:.25pt'>sim.</span></i></span><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US>1345).</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kalendarium,</span></b><span
lang=EN-US> </span><span lang=EN-US>-i</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>n.</span></i><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>script.</span></i><span lang=EN-US> </span><span
lang=EN-US>ca-<span style='letter-spacing:-1.75pt'>:</span></span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>l</span></i><i><span lang=EN-US
style='letter-spacing:-.75pt'>.</span></i><i><span lang=EN-US style='letter-spacing:
-1.75pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>22</span></i><span
lang=EN-US>.</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>al.</span></i><b><span lang=EN-US>[MFSP]</span></b><b><span
lang=EN-US>1</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>de</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>tabula</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>rationem</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>mensium</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>et</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>dierum</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>anni</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>variis</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>indiciis</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>additis</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>indicanti</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>i.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>q.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>tabula</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>temporum</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>–</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Kalender</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span
lang=EN-US>[MFSP]</span><b><span lang=EN-US>a</span></b><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>in</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>univ.</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Reinher.</span><span lang=EN-US style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span lang=EN-US style='font-variant:small-caps;
letter-spacing:.5pt'>Paderb.</span><span lang=EN-US> </span><span lang=EN-US>comput.</span><span
lang=EN-US> </span><span lang=EN-US>1,24</span><span lang=EN-US> </span><span
lang=EN-US>quod</span><span lang=EN-US> </span><span lang=EN-US>verae</span><span
lang=EN-US> </span><span lang=EN-US>accensiones</span><span lang=EN-US> </span><span
lang=EN-US>lunae</span><span lang=EN-US> </span><span lang=EN-US>diebus</span><span
lang=EN-US> </span><span lang=EN-US>certis</span><span lang=EN-US> </span><span
lang=EN-US>ascribantur</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kalendari</span></u>is.</span><span
lang=EN-US>[MFSP]</span><b><span lang=EN-US>b</span></b><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>necrologium,</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>liber</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>memoralis</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>–</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>‘Nekrolog’,</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Gedenkbuch</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Hugo</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Flav.</span><span
lang=EN-US> </span><span lang=EN-US>chron.</span><span lang=EN-US> </span>2 p. 380,31
constituit <i><span style='letter-spacing:.25pt'>(sc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>abbas)</span></i>,
ut in ‑<u><span style='display:none'>kalendari</span></u>o singulorum fratrum et
benefactorum aecclesiae, qui seculo excesserant, divisis paginis nomina, anniversaria,
quaque die in capitulo recitantur, diligentius annotato, quid quisque contulisset
aecclesiae, ut <span style='letter-spacing:2.25pt'>..</span>. recalesceret in eis
eorum memoria. <span style='font-variant:small-caps;letter-spacing:.5pt'>Liber</span>
ordin. Patav. 3,8 p. 973,14 in quo <i><span style='letter-spacing:.25pt'>(sc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>capitulo)</span></i>
mox ut anuntiatum fuerit c<a name="kalendarium1m_1"></a>‑<u><span
style='display:none'>alendari</span></u>um legit lector de omelia et recitatur tabula.
<i><span style='letter-spacing:.25pt'>al.</span></i>[MFSP]<b>c</b> <i><span
style='letter-spacing:.25pt'>catalogus</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>sanctorum,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>martyrologium</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Heiligenkalender,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‘Martyrologium’</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Vita</span>
Liutw. <span lang=EN-US>I</span><span lang=EN-US> </span><span lang=EN-US>6</span><span
lang=EN-US> </span><span lang=EN-US>cuius</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(oratorii)</span></i><span lang=EN-US> </span><span
lang=EN-US>dedicationis</span><span lang=EN-US> </span><span lang=EN-US>dies</span><span
lang=EN-US> </span><span lang=EN-US>eiusdem</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalendari</span></u>i</span><span
lang=EN-US> </span><span lang=EN-US>articulo</span><span lang=EN-US> </span><span
lang=EN-US>annotatur,</span><span lang=EN-US> </span><span lang=EN-US>quo</span><span
lang=EN-US> </span><span lang=EN-US>solemnitas</span><span lang=EN-US> </span><span
lang=EN-US>martyrii</span><span lang=EN-US> </span><span lang=EN-US>ipsius</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(Dionysii)</span></i><span
lang=EN-US> </span><span lang=EN-US>…</span><span lang=EN-US> </span><span
lang=EN-US>celebratur.</span><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Catal.</span><span
lang=EN-US> </span><span lang=EN-US>August.</span><span lang=EN-US> </span><span
lang=EN-US>(MGScript.</span><span lang=EN-US> </span><span lang=EN-US>XIII</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>278,28)</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kalendari</span></u>is</span><span
lang=EN-US> </span><span lang=EN-US>quibusdam</span><span lang=EN-US> </span><span
lang=EN-US>inventio</span><span lang=EN-US> </span><span lang=EN-US>et</span><span
lang=EN-US> </span><span lang=EN-US>translatio</span><span lang=EN-US> </span><span
lang=EN-US>eius</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>(sc.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Ciriaci</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>episcopi)</span></i><i><span
style='letter-spacing:.25pt'> </span></i>reperitur opinione magis quam ratione veritatis.<i><span
style='letter-spacing:.25pt'> </span></i><span style='font-variant:small-caps;
letter-spacing:.5pt'>Hugo</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span style='font-variant:small-caps;letter-spacing:
.5pt'>Trimb.</span> laur. 5 quoddam ‑<u><span style='display:none'>kalendari</span></u>um
sive letaniam tam per metrum varium quam per rudam viam annuo curriculo quidam compilavit.
<i><span style='letter-spacing:.25pt'>al.</span></i>[MFSP]<b>2</b> <i><span
style='letter-spacing:.25pt'>tabula</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>vectigalium,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>debitorum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Steuer-,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Schuldregister</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Dipl.</span>
Frid. <span lang=EN-US>I</span><span lang=EN-US> </span><span lang=EN-US>240</span><span
lang=EN-US> </span><span lang=EN-US>dabatur</span><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>tributum</span><span lang=EN-US> </span><span
lang=EN-US>secundum</span><span lang=EN-US> </span><span lang=EN-US>diversa</span><span
lang=EN-US> </span><span lang=EN-US>tempora</span><span lang=EN-US> </span><span
lang=EN-US>diverso</span><span lang=EN-US> </span><span lang=EN-US>modo,</span><span
lang=EN-US> </span><span lang=EN-US>alia</span><span lang=EN-US> </span><span
lang=EN-US>per</span><span lang=EN-US> </span><span lang=EN-US>quinquennium</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US style='letter-spacing:1.75pt'>.</span><span lang=EN-US>,</span><span
lang=EN-US> </span><span lang=EN-US>post</span><span lang=EN-US> </span><span
lang=EN-US>per</span><span lang=EN-US> </span><span lang=EN-US>singulos</span><span
lang=EN-US> </span><span lang=EN-US>annos</span><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US
style='letter-spacing:1.75pt'>.</span><span lang=EN-US>,</span><span
lang=EN-US> </span><span lang=EN-US>alia</span><span lang=EN-US> </span><span
lang=EN-US>per</span><span lang=EN-US> </span><span lang=EN-US>singulas</span><span
lang=EN-US> </span><span lang=EN-US>kalendas,</span><span lang=EN-US> </span><span
lang=EN-US>unde</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalendari</span></u>um</span><span lang=EN-US> </span><span
lang=EN-US>appellatur.</span><span lang=EN-US> </span><span style='font-variant:
small-caps;letter-spacing:.5pt'>Const.</span> imp. II 200,1 p. 266,22 dum debitorum
nostrorum cirographa legimus, dum ‑<u><span style='display:none'>kalendari</span></u>i
nostri nomina diligentissime perscrutamur <i><span style='letter-spacing:.25pt'>eqs.</span></i><i><span
style='letter-spacing:.25pt'> </span></i>(<i><span style='letter-spacing:.25pt'>sim.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><span style='font-variant:small-caps;
letter-spacing:.5pt'>Chart.</span> Friburg. 185 p. 156,29).[MFSP]<b>3</b> <i><span
style='letter-spacing:.25pt'>dies</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>mensis,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>qui</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>a</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>die</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>primo</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>enumeratur,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>determinatur</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>nach</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dem</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Monatsersten,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>den</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kalenden</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>gezählter,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>bestimmter</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Tag</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>des</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Monats</span></i>
<i><span style='color:black;letter-spacing:.25pt'>(cf.</span></i><i><span
style='color:black;letter-spacing:.25pt'> </span></i><i><span style='color:black;letter-spacing:-1.5pt'> </span><span style='color:black;letter-spacing:
.25pt'>p.</span></i><i><span style='color:black;letter-spacing:-1.75pt'> </span><span
style='color:black;letter-spacing:.25pt'>2541</span><span style='color:black;
letter-spacing:-1.5pt'>,</span></i><i><span style='color:black;letter-spacing:
-1.5pt'> </span><span style='color:black;letter-spacing:.25pt'>55</span><span
style='letter-spacing:.25pt'>sqq.)</span><span style='letter-spacing:-1.75pt'>:</span></i>
<span style='font-variant:small-caps;letter-spacing:.5pt'>Bern.</span><span
style='font-variant:small-caps;letter-spacing:.5pt'> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Const.</span><span
lang=EN-US> </span><span lang=EN-US>microl.</span><span lang=EN-US> </span><span
lang=EN-US>24</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>996</span><span lang=EN-US
style='font-size:7.0pt;position:relative;top:-2.0pt'>D</span><span lang=EN-US> </span><span
lang=EN-US>ieiunium</span><span lang=EN-US> </span><span lang=EN-US>aut</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kalendari</span></u>a</span><span
lang=EN-US> </span><span lang=EN-US>aliquando</span><span lang=EN-US> </span><span
lang=EN-US>aut</span><span lang=EN-US> </span><span lang=EN-US>lunationem</span><span
lang=EN-US> </span><span lang=EN-US>Martii</span><span lang=EN-US> </span><span
lang=EN-US>aut</span><span lang=EN-US> </span><span lang=EN-US>utrumque</span><span
lang=EN-US> </span><span lang=EN-US>simul</span><span lang=EN-US> </span><span
lang=EN-US>incurrit<span style='letter-spacing:-1.75pt'>:</span></span><span
lang=EN-US> </span><span lang=EN-US>Februarii</span><span lang=EN-US> </span><span
lang=EN-US>autem</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalendari</span></u>a</span><span lang=EN-US> </span><span
lang=EN-US>aliquando,</span><span lang=EN-US> </span><span lang=EN-US>lunationem</span><span
lang=EN-US> </span><span lang=EN-US>vero</span><span lang=EN-US> </span><span
lang=EN-US>nunquam</span><span lang=EN-US> </span><span lang=EN-US>attingit.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kalendarius,</b> -a, -um.[MFSP]<b>1</b><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>adi.</span><span
style='letter-spacing:-1.75pt'>:</span></i>[MFSP]<b>a</b> <i><span
style='letter-spacing:.25pt'>spectat</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>ad</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kalendas</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>i.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ad</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kalendas</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>pertinens</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>auf</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>die</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kalenden</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>bezogen</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Bernold.</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span style='font-variant:small-caps;letter-spacing:
.5pt'>Const.</span> chron. p. 393,27 (ed. Pertz) Aegiptii et Romani <span
style='letter-spacing:2.25pt'>..</span><span style='letter-spacing:1.75pt'>.</span>,
quem primum decennovenalis cycli annum habere instituerunt, eiusdem anni ‑<u><span
style='display:none'>kalendari</span></u>a<a name="kalendae7m_1"></a>s lunae aetates
pro regularibus per totum eundem cyclum tenere decreverunt <i><span
style='letter-spacing:.25pt'>(<span style='color:black'>cf.</span></span></i><i><span
style='color:black;letter-spacing:.25pt'> </span></i><i><span style='color:black;letter-spacing:-1.5pt'> </span><span style='color:black;letter-spacing:
.25pt'>p.</span></i><i><span style='color:black;letter-spacing:-1.75pt'> </span><span
style='color:black;letter-spacing:.25pt'>2542</span><span style='color:black;
letter-spacing:-1.5pt'>,</span></i><i><span style='color:black;letter-spacing:
-1.5pt'> </span><span style='color:black;letter-spacing:.25pt'>56</span><span
style='letter-spacing:.25pt'>)</span></i>.[MFSP]<b>b</b> <i><span
style='letter-spacing:.25pt'>spectat</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>ad</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>diem</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>obitus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>in</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kalendario</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>inscriptum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>i.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ad</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kalendarium,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>tabulam</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(sanctorum)</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>pertinens</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>auf</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>den</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(Heiligen)Kalender</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>bezogen,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kalendarisch</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Milo</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span style='font-variant:small-caps;letter-spacing:
.5pt'>Mind.</span> ad Imm. (AnalBoll. 18. 1899. p. 19,6; s. X.<span
style='font-size:7.0pt;position:relative;top:-2.0pt'>ex.</span>) quorum <i><span
style='letter-spacing:.25pt'>(sc.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>Gorgonii</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>et</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Dorothei)</span></i>
<span style='letter-spacing:2.25pt'>..</span>. passionem sub eodem ‑<u><span
style='display:none'>kalendari</span></u>o numero inventam <span
style='letter-spacing:2.25pt'>..</span>. vestrae caritati dirigere destinabam. <span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Epist.</span><span
lang=EN-US> </span><span lang=EN-US>Teg.</span><span lang=EN-US> </span><span
lang=EN-US>I</span><span lang=EN-US> </span><span lang=EN-US>22</span><span
lang=EN-US> </span><span lang=EN-US>diem</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalendari</span></u>um</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(ed.,</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US>ka</span><span
lang=EN-US style='font-family:"Cambria",serif'>ł</span><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>cod.)</span></i><span lang=EN-US> </span><span lang=EN-US>iubete</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>comes)</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US>conscribi</span><span
lang=EN-US> </span><span lang=EN-US>membrana</span><span lang=EN-US> </span><span
lang=EN-US>nobisque</span><span lang=EN-US> </span><span lang=EN-US>transmitti</span><span
lang=EN-US> </span><span lang=EN-US>per</span><span lang=EN-US> </span><span
lang=EN-US>presentem</span><span lang=EN-US> </span><span lang=EN-US>pelligerum.</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Honor.</span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>August.</span><span lang=EN-US> </span><span lang=EN-US>gemm.</span><span
lang=EN-US> </span><span lang=EN-US>3,125</span><span lang=EN-US> </span><span
lang=EN-US>quod</span><span lang=EN-US> </span><span lang=EN-US>passio</span><span
lang=EN-US> </span><span lang=EN-US>Domini</span><span lang=EN-US> </span><span
lang=EN-US>vel</span><span lang=EN-US> </span><span lang=EN-US>resurrectio</span><span
lang=EN-US> </span><span lang=EN-US>non</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalendari</span></u>a</span><span lang=EN-US> </span><span
lang=EN-US>die</span><span lang=EN-US> </span><span lang=EN-US>agitur,</span><span
lang=EN-US> </span><span lang=EN-US>haec</span><span lang=EN-US> </span><span
lang=EN-US>causa</span><span lang=EN-US> </span><span lang=EN-US>est,</span><span
lang=EN-US> </span><span lang=EN-US>quod</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>eqs.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>al.</span></i><span lang=EN-US>[MFSP]</span><b><span lang=EN-US>c</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>i<a
name="kalendae6m_1"></a>unctura</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><span lang=EN-US>fratres</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalendari</span></u>i</span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>i.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>q.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>fratres</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>kalendarum</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>q.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>d.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>–</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>sog.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>‘Kalandsbruderschaft’</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(de</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>re</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>op.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>cit.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>[</span></i><i><span style='letter-spacing:-1.5pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>2542</span><span
style='letter-spacing:-1.5pt'>,</span></i><i><span style='letter-spacing:-1.5pt'>
</span><span style='letter-spacing:.25pt'>63])</span><span style='letter-spacing:
-1.75pt'>:</span></i>[MFSP]<span style='font-variant:small-caps;letter-spacing:
.5pt'>Chart.</span> Westph. <span lang=EN-US>IV</span><span lang=EN-US> </span><span
lang=EN-US>234</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>155,24</span><span lang=EN-US> </span><span
lang=EN-US>(a.</span><span lang=EN-US> </span><span lang=EN-US>1234)</span><span
lang=EN-US> </span><span lang=EN-US>si</span><span lang=EN-US> </span><span
lang=EN-US>nobis</span><span lang=EN-US> </span><span lang=EN-US>et</span><span
lang=EN-US> </span><span lang=EN-US>fratribus</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalendari</span></u>is</span><span
lang=EN-US> </span><span lang=EN-US>locus</span><span lang=EN-US> </span><span
lang=EN-US>ille</span><span lang=EN-US> </span><span lang=EN-US>videbitur</span><span
lang=EN-US> </span><span lang=EN-US>incommodus,</span><span lang=EN-US> </span><span
lang=EN-US>per</span><span lang=EN-US> </span><span lang=EN-US>nos</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>fratres</span><span lang=EN-US> </span><span lang=EN-US>‑<u><span
style='display:none'>kalendari</span></u>os</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>alium</span><span
lang=EN-US> </span><span lang=EN-US>locum</span><span lang=EN-US> </span><span
lang=EN-US>poterit</span><span lang=EN-US> </span><span lang=EN-US>transmutari</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>eqs.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>ibid.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>al.</span></i></p>

<p class=MsoNormal style='text-indent:6.5pt'><b>2</b> <i><span
style='letter-spacing:.25pt'>subst.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>masc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>i.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>certus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dies</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>mensis,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>anni</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Monats-,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kalendertag</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Heimo</span><span
style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
style='font-variant:small-caps;letter-spacing:.5pt'>Bamb.</span> chron. 3,22 capit.
<span lang=EN-US>245</span><span lang=EN-US> </span><span lang=EN-US>supputatio</span><span
lang=EN-US> </span><span lang=EN-US>temporis</span><span lang=EN-US> </span><span
lang=EN-US>propheticarum</span><span lang=EN-US> </span><span lang=EN-US>ebdomadum</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>quo</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kalendari</span></u>o</span><span
lang=EN-US> </span><span lang=EN-US>incipiantur</span><span lang=EN-US> </span><span
lang=EN-US>vel</span><span lang=EN-US> </span><span lang=EN-US>finiantur.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kalendaticum</b>
(ca‑), -i <i><span style='letter-spacing:.25pt'>n.</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>vectigal</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>kalendis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Ianuariis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>solvendum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>am</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ersten</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Januar</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>zu</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>entrichtende</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Abgabe</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Chart.</span> Ital. Ficker 192,1 p. 233,32 (a. 1196) ego Henricus
de Frascarolio sindicus <span style='letter-spacing:2.25pt'>..</span>. conqueror
nomine ipsius episcopi <i><span style='letter-spacing:.25pt'>(sc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Vercellensis)</span></i>
<span style='letter-spacing:2.25pt'>..</span>. de ripatico, piscariis, c‑<u><span
style='display:none'>alendatic</span></u>o (c‑<u><span style='display:none'>alend</span></u>arico
<i><span style='letter-spacing:.25pt'>ed.</span></i>) <i><span
style='letter-spacing:.25pt'>eqs</span></i>. 192,2 p. 235,41 item dicebat <i><span
style='letter-spacing:.25pt'>(sc.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>syndicus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Casalis)</span></i>,
quod ripaticum et piscariae, c‑<u><span style='display:none'>alendatic</span></u>um
et curadia <span style='letter-spacing:2.25pt'>..</span>. ad ecclesiam Vercellensem
seu episcopum non pertinebant. <i><span style='letter-spacing:.25pt'>ibid.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>al.</span></i></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kalendula</b> (ca‑), 
-ae <i><span style='letter-spacing:.25pt'>f.</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>(orig.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>inc.;</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>H.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Genaust,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Etymologisches</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Wb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>d.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>botan.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Pflanzennamen.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span style='font-size:7.0pt;
position:relative;top:-2.0pt;letter-spacing:.25pt'>3</span><span
style='letter-spacing:.25pt'>1996.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>116)</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>Calendula</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>officinalis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>L.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Ringelblume</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Marzell,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Wb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dt.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Pflanzennam.,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>I.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>715sqq.;</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>usu</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>medic.)</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Tract.</span>
de aegr. cur. p. 283,33 fiat subfumigium et fomentum ex ‑<u><span
style='display:none'>kalendul</span></u>a et tapso barbasso decoctis in vino albo.
<span lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Gloss.</span><span
lang=EN-US> </span><span lang=EN-US>Roger.</span><span lang=EN-US> </span><span
lang=EN-US>I</span><span lang=EN-US> </span><span lang=EN-US>A</span><span
lang=EN-US> </span><span lang=EN-US>2,9</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>608,41</span><span
lang=EN-US> </span><span lang=EN-US>coquatur</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kalendul</span></u>a</span><span
lang=EN-US> </span><span lang=EN-US>cum</span><span lang=EN-US> </span><span
lang=EN-US>multo</span><span lang=EN-US> </span><span lang=EN-US>sale</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>aqua</span><span lang=EN-US> </span><span lang=EN-US>vel</span><span
lang=EN-US> </span><span lang=EN-US>vino.</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Wilh.</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Cong.</span><span
lang=EN-US> </span><span lang=EN-US>chirurg.</span><span lang=EN-US> </span><span
lang=EN-US>1416</span><span lang=EN-US> </span><span lang=EN-US>c‑<u><span
style='display:none'>alendul</span></u>a</span><span lang=EN-US> </span><span
lang=EN-US>decocta</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>aqua</span><span lang=EN-US> </span><span
lang=EN-US>cum</span><span lang=EN-US> </span><span lang=EN-US>multo</span><span
lang=EN-US> </span><span lang=EN-US>sale</span><span lang=EN-US> </span><span
lang=EN-US>tepida</span><span lang=EN-US> </span><span lang=EN-US>circumligetur.</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>al.</span></i></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kaliphus</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>calipha.</span><span lang=EN-US>[VERWEIS]</span><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kalixtia</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>caristia.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kallendae</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> kalendae.[VERWEIS]<b>kallidus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. callidus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kallos</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>callos.</span><span lang=EN-US>[MFSP]</span><i><span lang=EN-US
style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>II.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>88,8</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Albert.</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span lang=EN-US style='font-variant:small-caps;
letter-spacing:.5pt'>M.</span><span lang=EN-US> </span><span lang=EN-US>div.</span><span
lang=EN-US> </span><span lang=EN-US>nom.</span><span lang=EN-US> </span><span
lang=EN-US>4,77</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>186,26</span><span lang=EN-US> </span><span
lang=EN-US>pulchrum</span><span lang=EN-US> </span><span lang=EN-US>apud</span><span
lang=EN-US> </span><span lang=EN-US>Graecos</span><span lang=EN-US> </span><span
lang=EN-US>dicitur</span><span lang=EN-US> </span><span lang=EN-US>k‑<u><span
style='display:none'>allo</span></u>s.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kalo</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 4. calo.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kalodemon</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>calodaemon.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kaloius</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>coloeos.</span><span lang=EN-US>[MFSP]</span><i><span lang=EN-US
style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>II.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>881,7</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Albert.</span><span
style='font-variant:small-caps;letter-spacing:.5pt'> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>M.</span><span lang=EN-US> </span><span
lang=EN-US>eth.</span><span lang=EN-US> </span><span lang=EN-US>I</span><span
lang=EN-US> </span><span lang=EN-US>695</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>595,30sqq.</span><span
lang=EN-US> </span><span lang=EN-US>dicunt,</span><span lang=EN-US> </span><span
lang=EN-US>quod</span><span lang=EN-US> </span><span lang=EN-US>‘similis’</span><span
lang=EN-US> </span><span lang=EN-US>ad</span><span lang=EN-US> </span><span
lang=EN-US>‘similem’</span><span lang=EN-US> </span><span lang=EN-US>coniungitur</span><span
lang=EN-US> </span><span lang=EN-US>amicitia,</span><span lang=EN-US> </span><span
lang=EN-US>ibi</span><span lang=EN-US> </span><span lang=EN-US>‘et</span><span
lang=EN-US> </span><span lang=EN-US>kaloius</span><span lang=EN-US> </span><span
lang=EN-US>ad</span><span lang=EN-US> </span><span lang=EN-US>kaloium’</span><span
lang=EN-US> </span><span lang=EN-US>(<i><span style='letter-spacing:.25pt'>p.</span></i></span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>1155</span></i><i><span lang=EN-US
style='font-size:7.0pt;position:relative;top:-2.0pt;letter-spacing:.25pt'>a</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>,32</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US style='font-family:
OldGreekSerif;letter-spacing:.25pt'>koloiòn</span><span lang=EN-US
style='letter-spacing:.25pt'> </span><span lang=EN-US style='font-family:OldGreekSerif;
letter-spacing:.25pt'>potì</span><span lang=EN-US style='letter-spacing:.25pt'>
</span><span lang=EN-US style='font-family:OldGreekSerif;letter-spacing:.25pt'>koloión</span><span
lang=EN-US>),</span><span lang=EN-US> </span><span lang=EN-US>id</span><span
lang=EN-US> </span><span lang=EN-US>est</span><span lang=EN-US> </span><span
lang=EN-US>amicabilis</span><span lang=EN-US> </span><span lang=EN-US>et</span><span
lang=EN-US> </span><span lang=EN-US>socialis</span><span lang=EN-US> </span><span
lang=EN-US>ad</span><span lang=EN-US> </span><span lang=EN-US>eum,</span><span
lang=EN-US> </span><span lang=EN-US>qui</span><span lang=EN-US> </span><span
lang=EN-US>est</span><span lang=EN-US> </span><span lang=EN-US>huiusmodi</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>eqs</span></i><span
lang=EN-US>.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kalomalis</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>calamaris.[VERWEIS]<b>kalor</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> calor.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kalos</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> calos.[VERWEIS]<b>kamaleon</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> chamaeleon.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kambalcha</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>balcha.[VERWEIS]<b>kamellus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> camillus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kamenata,</b><b>
</b><span style='font-size:6.0pt;font-family:Wingdings;position:relative;
top:-2.0pt'></span><b>kaminata</b> <i><span style='letter-spacing:.25pt'>v.</span></i>
<span style='font-family:Symbol;position:relative;top:-1.0pt'>*</span>caminata.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kamisia</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> camis(i)a.[VERWEIS]<b>kanale</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. canalis.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kaniparius</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> canabarius.[VERWEIS]<b>kanna</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> canna.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kanon,</span></b><b><span
lang=EN-US> </span></b><b><span lang=EN-US>kanonicus</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>ca-.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kapella,</span></b><b><span lang=EN-US> </span></b><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kapilla</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
lang=EN-US>2.</span><span lang=EN-US> </span><span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>capella.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kappa</b> v. 1. cappa.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kappalanus</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> 1. <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>capellanus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kapsa</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> capsa.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karabitus</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>carabitus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>karact-</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>charact-.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>karat</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>caratum.</span><span lang=EN-US>[MFSP]</span><i><span lang=EN-US
style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>II.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>266,41</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Thadd.</span><span
style='font-variant:small-caps;letter-spacing:.5pt'> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Florent.</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US>cons.</span><span lang=EN-US> </span><span lang=EN-US>125,80</span><span
lang=EN-US> </span><span lang=EN-US>postquam</span><span lang=EN-US> </span><span
lang=EN-US>cocta</span><span lang=EN-US> </span><span lang=EN-US>fuerint</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>species)</span></i><span lang=EN-US>,</span><span
lang=EN-US> </span><span lang=EN-US>dissolvantur</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>eo</span><span
lang=EN-US> </span><span lang=EN-US>oppoponaci</span><span lang=EN-US> </span><span
lang=EN-US>et</span><span lang=EN-US> </span><span lang=EN-US>bdelii,</span><span
lang=EN-US> </span><span lang=EN-US>ana</span><span lang=EN-US> </span><span
lang=EN-US>k‑<u><span style='display:none'>ara</span></u>t</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>i</span><span lang=EN-US>,</span><span lang=EN-US> </span><span
lang=EN-US>olei</span><span lang=EN-US> </span><span lang=EN-US>rutacei</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>mellis</span><span lang=EN-US> </span><span lang=EN-US>ana</span><span
lang=EN-US> </span><span lang=EN-US>drachmas</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>x</span><span
lang=EN-US>.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>karaxatio</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>charaxatio.</span><span lang=EN-US>[VERWEIS]</span><b><span
lang=EN-US>karcer</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
lang=EN-US>carcer.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>karcharodus</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>carcharodus.</span><span lang=EN-US>[VERWEIS]</span><b><span
lang=EN-US>kardinalis</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
lang=EN-US>cardinalis.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karecter</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> character.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karena</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> 2. <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>carina.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karibdis</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> charybdis.[VERWEIS]<b>kariga</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> carica.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karina</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 2. <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>carina.[VERWEIS]<b>kariptis</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> charybdis.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karisma</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> charisma.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karistia</b>
<i><span style='letter-spacing:.25pt'>v.</span></i><i><span style='letter-spacing:
.25pt'> </span></i><span style='font-family:Symbol;position:relative;
top:-1.0pt'>*</span>caristia.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karitas,</b><b> </b><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karitativus</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> ca-.[VERWEIS]<b>karmen</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> carmen.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karo</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> caro.[VERWEIS]<b>[karobe</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cacabre.<b>]</b></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>karolensis</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>carol(in)ensis.</span><span lang=EN-US>[VERWEIS]</span><b><span
lang=EN-US>[karolicos</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
lang=EN-US>catholicus.<b>]</b></span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>Karolida,</b> -ae
<i><span style='letter-spacing:.25pt'>m.</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>progenies</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>Karoli</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(Magni)</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Nachkomme</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Karls</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(des</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Großen)</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Geneal.</span> Brab. app. 8 (MGScript. XXV p. 395,18; c. 1270/71)
Iohannes dux Lotharingie et Brabantie <span style='letter-spacing:2.25pt'>..</span><span
style='letter-spacing:1.75pt'>.</span>, duodecimus K‑<u><span style='display:
none'>arolid</span></u>arum a Karolo duce, qui Franciam amisit sibi debitam.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karolinensis</b><b>
</b><i><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>carol(in)ensis.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karopos</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>charopos.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karpentarius</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> carpentarius.[VERWEIS]<b>karpo</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. carpo.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karpos</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> carpos.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karrada</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>carrada.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karralis</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>carralis.[VERWEIS]<span style='font-size:
6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karrena,</b><b>
</b><span style='font-size:6.0pt;font-family:Wingdings;position:relative;
top:-2.0pt'></span><b>karrina</b> <i><span style='letter-spacing:.25pt'>v.</span></i>
2. <span style='font-family:Symbol;position:relative;top:-1.0pt'>*</span>carina.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karrinarius</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>carinarius.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karrotium</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>carrocium.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karruca</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> carruca.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>karrucium</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>carrocium.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>karta</b><b> </b><i><span
style='letter-spacing:.25pt'>sim.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i> cha- <i><span
style='letter-spacing:.25pt'>praeter</span><span style='letter-spacing:-1.75pt'>:</span></i></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><span class=lemma>kartata</span><b>,</b>
-ae <i><span style='letter-spacing:.25pt'>f.</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>(theod.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>vet.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kartât</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ex</span></i><i><span
style='letter-spacing:.25pt'> </span></i>caritas<i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>[cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Lexer,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Mittelhochdt.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Handwb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>I.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>1523sq.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>et</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>2147</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>s.v.</span></i><i><span
style='letter-spacing:.25pt'> </span></i>minne-brôt<i><span style='letter-spacing:
.25pt'>;</span></i> <i><span style='letter-spacing:.25pt'>Mittelniederdt.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Handwb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>II.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>524.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>522</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>s.v.</span></i><i><span
style='letter-spacing:.25pt'> </span></i>karitâte<i><span style='letter-spacing:
.25pt'>)</span></i>[MFSP]<i><span style='letter-spacing:.25pt'>de</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>pane</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>plebano</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>et</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dominabus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>conventus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>competenti</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>i.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>panis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>extraordinarius,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>pro</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>caritate</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>datus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Brotzulage,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>-spende,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‘Minnebrot’</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Registr.</span> Geisenf. 26 in festo sancti Michahelis, cum
afferuntur reditus et panes, <span style='letter-spacing:2.25pt'>..</span>. debent
plebano dari <span style='letter-spacing:2.25pt'>..</span>. duo panes, qui dicuntur
‑<u><span style='display:none'>kartat</span></u>e (gloss.<span
style='letter-spacing:-1.75pt'>:</span> minnbrot), <span style='letter-spacing:
2.25pt'>..</span>. item cuilibet domne de conventu <span style='font-variant:
small-caps;letter-spacing:.5pt'>IIII</span><span style='font-size:7.0pt;
position:relative;top:-2.0pt'>or</span> panes unacum ‑<u><span
style='display:none'>kartat</span></u>a.[VERWEIS]<i><span style='letter-spacing:
.25pt'>cf.</span></i> caritas.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kartha</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> charta.[VERWEIS]<b>karum</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> carrum.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kasta</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>casta.[VERWEIS]<span style='font-size:
6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>katabulum</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> 2. <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>catabulum.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>katafatkus</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>cataphaticus.</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>adde</span></i><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>ad</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>vol.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>II.</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>361,14</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Theod.</span><span
style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
style='font-variant:small-caps;letter-spacing:.5pt'>Trev.</span> phys. 782 divina
cuncta sint, quam produnt preclua palam, apofatke sit vel ista, k‑<u><span
style='display:none'>ata</span></u>fatk vel illa <i><span style='letter-spacing:
.25pt'>(v.</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>notam</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>ed.)</span></i>. <i><span
style='letter-spacing:.25pt'>ibid.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>al.</span></i></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>[</span></b><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>katakothimus</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><span style='font-family:Symbol;position:relative;
top:-1.0pt'>*</span><span lang=EN-US>catocochimos.</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>II.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>p.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>383,6</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span
lang=EN-US>[MFSP]</span><i><span lang=EN-US style='letter-spacing:.25pt'>usu</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>subst.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>neutr.</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Albert.</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>M.</span><span
lang=EN-US> </span><span lang=EN-US>eth.</span><span lang=EN-US> </span><span
lang=EN-US>I.</span><span lang=EN-US> </span><span lang=EN-US>938</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>782,46</span><span lang=EN-US> </span><span lang=EN-US>‘sermones</span><span
lang=EN-US> </span><span lang=EN-US style='letter-spacing:2.25pt'>..</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>morales’</span><span
lang=EN-US> </span><span lang=EN-US>exhortatorii,</span><span lang=EN-US> </span><span
lang=EN-US>quamvis</span><span lang=EN-US> </span><span lang=EN-US>‘provocent’</span><span
lang=EN-US> </span><span lang=EN-US>ad</span><span lang=EN-US> </span><span
lang=EN-US>‘bonum</span><span lang=EN-US> </span><span lang=EN-US>liberalem</span><span
lang=EN-US> </span><span lang=EN-US>iuvenem’,</span><span lang=EN-US> </span><span
lang=EN-US style='font-family:"StplGaramondAkzente Normal",serif'>&lt;</span><span
lang=EN-US>qui</span><span lang=EN-US> </span><span lang=EN-US>est</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>‘amore</span><span lang=EN-US> </span><span lang=EN-US>boni’</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>‘faciat</span><span lang=EN-US> </span><span lang=EN-US>utique</span><span
lang=EN-US> </span><span lang=EN-US>k‑<u><span style='display:none'>atakothim</span></u>um’</span><span
lang=EN-US style='font-family:"StplGaramondAkzente Normal",serif'>&gt;</span><span
lang=EN-US> </span><span lang=EN-US>(<i><span style='letter-spacing:.25pt'>cf.</span></i></span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>p.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>1180</span></i><i><span
lang=EN-US style='font-size:7.0pt;position:relative;top:-2.0pt;letter-spacing:
.25pt'>a</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>,7sq.</span></i><span
lang=EN-US> </span><span style='font-family:OldGreekSerif;letter-spacing:.25pt'>©pakousoménwn</span><span
style='letter-spacing:.25pt'> </span><span style='font-family:OldGreekSerif;
letter-spacing:.25pt'>tôn</span><span style='letter-spacing:.25pt'> </span><span
style='font-family:OldGreekSerif;letter-spacing:.25pt'>™pieikôß</span><span
style='letter-spacing:.25pt'> </span><span style='font-family:OldGreekSerif;
letter-spacing:.25pt'>toîß</span><span style='letter-spacing:.25pt'> </span><span
style='font-family:OldGreekSerif;letter-spacing:.25pt'>Éqesi</span><span
style='letter-spacing:.25pt'> </span><span style='font-family:OldGreekSerif;
letter-spacing:.25pt'>prohgménwn</span>), idest universaliter repletum ‘virtute’
et honorabilitate <i><span style='letter-spacing:.25pt'>eqs</span></i>.<b>]</b></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>katapant,</b><b>
</b><span style='font-size:6.0pt;font-family:Wingdings;position:relative;
top:-2.0pt'></span><b>katapanus</b> <i><span style='letter-spacing:.25pt'>v.</span></i>
<span style='font-family:Symbol;position:relative;top:-1.0pt'>*</span>catapanus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kataphaticus</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>cataphaticus.[VERWEIS]<b>katapotia</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> catapotia.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kataracta</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>cataracta.</span><span lang=EN-US>[VERWEIS]</span><b><span
lang=EN-US>katarrhus</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
lang=EN-US>catarrhus.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kategoria</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>categoria.</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>II.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>p.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>369,44</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span
lang=EN-US>[MFSP]</span><b><span lang=EN-US>3</span></b><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>theol.</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Theod.</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
style='font-variant:small-caps;letter-spacing:.5pt'>Trev.</span> phys. 90 sane <span
style='font-family:OldGreekSerif;letter-spacing:.25pt'>qeoloGor</span><span
style='font-size:9.0pt'>um</span> verba catholicorum fore <span
style='font-family:OldGreekSerif;letter-spacing:.25pt'>orqoDwca</span> perstat k‑<u><span
style='display:none'>ategori</span></u>a <span style='font-family:OldGreekSerif;
letter-spacing:.25pt'>upo-</span> principales ‑<span style='font-family:OldGreekSerif;
letter-spacing:.25pt'>ktasis</span><span style='letter-spacing:.25pt'> </span><span
style='font-family:OldGreekSerif;letter-spacing:.25pt'>usioses</span> tres substantialitate
<span style='font-size:9.0pt'>y</span><span style='font-family:OldGreekSerif;
letter-spacing:.25pt'>fistasis</span> in <span style='font-family:OldGreekSerif;
letter-spacing:.25pt'>enai</span> <i><span style='letter-spacing:.25pt'>(v.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>notam</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ed.)</span></i>.
<i><span lang=EN-US style='letter-spacing:.25pt'>ibid.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>al.</span></i></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kategorizo</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>categorizo.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>[katenphatos</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US>cacemphatus.</span><span
lang=EN-US>[MFSP]</span><i><span lang=EN-US style='letter-spacing:.25pt'>adde</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>II.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>p.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>9,8</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>masc.</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Conr.</span><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'> </span><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Mur.</span><span lang=EN-US> </span><span
lang=EN-US>summ.</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>55,9</span><span lang=EN-US> </span><span
lang=EN-US>quartum</span><span lang=EN-US> </span><span lang=EN-US>vitium</span><span
lang=EN-US> </span><span lang=EN-US>est</span><span lang=EN-US> </span><span
lang=EN-US>katen‑<u><span style='display:none'>phat</span></u>os,</span><span
lang=EN-US> </span><span lang=EN-US>cum</span><span lang=EN-US> </span><span
lang=EN-US>precedens</span><span lang=EN-US> </span><span lang=EN-US>dictio</span><span
lang=EN-US> </span><span lang=EN-US>terminatur</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>‘m’</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>sequens</span><span lang=EN-US> </span><span lang=EN-US>incipit</span><span
lang=EN-US> </span><span lang=EN-US>ab</span><span lang=EN-US> </span><span
lang=EN-US>eadem</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>eqs</span></i><span lang=EN-US>.<b>]                            </b><span
style='color:#5B9BD5'>[EndeLemmaStreckeAutor]</span><i><span style='letter-spacing:
.25pt'>Häberlin</span></i></span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>katerva</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>caterva.</span><span lang=EN-US>[VERWEIS]</span><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>katfige</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>cataphyge.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kathegoricus</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>categoricus.</span><span lang=EN-US>[VERWEIS]</span><b><span
lang=EN-US>kathena</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
lang=EN-US>catena.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kathinia</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>cadmia.</span><span lang=EN-US>[VERWEIS]</span><b><span
lang=EN-US>katholicus</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
lang=EN-US>catholicus.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>katowa</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>catowa.[VERWEIS]<b>kattus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cattus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><span class=lemma>kavenna</span><b>,</b><b>
</b>‑ae <i><span style='letter-spacing:.25pt'>f.</span></i>  <span class=jofu2><span
style='font-size:8.0pt;font-family:"Arial",sans-serif;color:#0070C0;letter-spacing:
0pt'>Mandrin</span></span>[MFSP]  (<i><span style='letter-spacing:.25pt'>francog.</span></i>
chevanne, chevenne; <i><span style='letter-spacing:.25pt'>cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Wartburg,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Frz.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>etym.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Wb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>II.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>264</span></i><i><span
style='font-size:7.0pt;position:relative;top:-2.0pt;letter-spacing:.25pt'>b</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>s.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span></i>capito)[MFSP]<i><span
style='letter-spacing:.25pt'>Leuciscus</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>idus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Aland,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Gängling,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Rotten</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(de</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>re</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Grzimeks</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Tierleben.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>IV.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span style='font-size:7.0pt;
position:relative;top:-2.0pt;letter-spacing:.25pt'>2</span><span
style='letter-spacing:.25pt'>1980.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>330sq.)</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Consuet.</span> Vird. 23 habebunt <i><span
style='letter-spacing:.25pt'>fratres</span></i> haec piscium genera<span
style='letter-spacing:-1.75pt'>:</span> capitonum, bar, ‑<u><span
style='display:none'>kavenn</span></u>arum <i><span style='letter-spacing:.25pt'>eqs</span></i>.
<i><span style='letter-spacing:.25pt'>(v.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>notam</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ed.)</span></i>.[VERWEIS]<i><span
style='letter-spacing:.25pt'>cf.</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-family:Symbol;position:relative;top:-1.0pt'>*</span>cavedanus,
<span style='font-family:Symbol;position:relative;top:-1.0pt'>*</span>cavena.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kaus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> chaos.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kebulus</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>chebulus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kecabre</b> <i><span
style='letter-spacing:.25pt'>v.</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-family:Symbol;position:relative;top:-1.0pt'>*</span>cacabre.[VERWEIS]<b>kecaumenos</b>
<i><span style='letter-spacing:.25pt'>v.</span></i><i><span style='letter-spacing:
.25pt'> </span></i>cecaumenus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kefalargicus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cephalargicus.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kekabie</b>
<i><span style='letter-spacing:.25pt'>v.</span></i><i><span style='letter-spacing:
.25pt'> </span></i><span style='font-family:Symbol;position:relative;
top:-1.0pt'>*</span>cacabre.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kelinus,</b> ‑a,
‑um.[MFSP]<i><span style='letter-spacing:.25pt'>(theod.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>vet.</span></i>
kela; <i><span style='letter-spacing:.25pt'>cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Ahd.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Wb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>V.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>73sq.)</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>ad</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>guttur</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>pertinens,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>collo</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>circumpositus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>zur</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kehle</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>gehörig,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>den</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Nacken</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>umschließend</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Cod</span>.
Eberh. I p. 151,5 quod <span style='letter-spacing:2.25pt'>..</span>. Ludewicus,
filius Karoli, hoc privilegium clericis canonicam regulam servantibus dederit, ut
‑<u><span style='display:none'>kelin</span></u>a lappa, hoc est rubeo pelliciorum
ornatu, utantur.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kembelinus</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US>camelinus.</span><span
lang=EN-US>[MFSP]</span><i><span lang=EN-US style='letter-spacing:.25pt'>adde</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>II.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>p.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>108,31sqq.</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Chart.</span><span
lang=EN-US> </span><span lang=EN-US>Wirt.</span><span lang=EN-US> </span><span
lang=EN-US>1637</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>31,35</span><span lang=EN-US> </span><span
lang=EN-US>habeant</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>sorores</span></i><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>de</span><span lang=EN-US> </span><span
lang=EN-US>nigro</span><span lang=EN-US> </span><span lang=EN-US>barrechano</span><span
lang=EN-US> </span><span lang=EN-US>vel</span><span lang=EN-US> </span><span
lang=EN-US>alio</span><span lang=EN-US> </span><span lang=EN-US>nigro</span><span
lang=EN-US> </span><span lang=EN-US>panno</span><span lang=EN-US> </span><span
lang=EN-US>vel</span><span lang=EN-US> </span><span lang=EN-US>de</span><span
lang=EN-US> </span><span lang=EN-US>fusco</span><span lang=EN-US> </span><span
lang=EN-US>kemb‑<u><span style='display:none'>elin</span></u>o</span><span
lang=EN-US> </span><span lang=EN-US>pallia</span><span lang=EN-US> </span><span
lang=EN-US>minora.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kemeto</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>kmet(h)o.[VERWEIS]<b>kemmelinus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i><i><span style='letter-spacing:.25pt'>
</span></i>camelinus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kenkel</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> conchylium.[VERWEIS]<b>kenodoxia</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> cenodoxia.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kere</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> chaere.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kerena</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> 2. <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>carina.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kerna</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cherua.[VERWEIS]<span style='font-size:
6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kerno</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cherno.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>ketoniti</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>coetonites.[VERWEIS]<b>kianos</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cyaneus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>[kicles</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> helix.<b>]</b>[VERWEIS]<b>[kidion</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> sidia.<b>]</b></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kilegunda</b> <i><span
style='letter-spacing:.25pt'>vel</span></i> <span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kiligunda,</b> ‑ae
<i><span style='letter-spacing:.25pt'>f.</span></i>[MFSP](<i><span
style='letter-spacing:.25pt'>finnice</span></i><i><span style='letter-spacing:
.25pt'> </span></i>kihlakunta, <i><span style='letter-spacing:.25pt'>estnice</span></i>
kihelkond)[MFSP]<i><span style='letter-spacing:.25pt'>script.</span><span
style='letter-spacing:-1.75pt'>:</span></i>[MFSP]si‑<span style='letter-spacing:
-1.75pt'>:</span> <i><span style='letter-spacing:.25pt'>l</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>57</span></i>.[MFSP]kyl‑<span
style='letter-spacing:-1.75pt'>:</span> <i><span style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>57</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>63</span></i>.[MFSP]<i><span
style='letter-spacing:.25pt'>districtus</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>(parvus)</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>administrativus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(kleiner)</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Verwaltungsbezirk,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‘Harde’</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(de</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>re</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>L.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Arbusow,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>DtArch.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>8.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>1951.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>148</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>c.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>adn.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>8)</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Heinr.</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span style='font-variant:small-caps;letter-spacing:
.5pt'>Lett</span>. chron. 28,2 episcopo Rigensi Maritimam cum septem kile‑<u><span
style='display:none'>gund</span></u>is (s<a name="kavenn18m_1"></a>ile‑<u><span
style='display:none'>gundis</span></u> <i><span style='letter-spacing:.25pt'>S,</span></i>
kili‑<u><span style='display:none'>gundis</span></u> <i><span style='letter-spacing:
.25pt'>T,</span></i> k<a name="kavenn19m_1"></a>yle‑<u><span style='display:
none'>gundis</span></u> <i><span style='letter-spacing:.25pt'>o</span></i>) attribuerunt
<i><span style='letter-spacing:.25pt'>fratres</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>militiae</span></i>
<i><span style='letter-spacing:.25pt'>(v.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>notam</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ed.)</span></i>.
<i><span lang=EN-US style='letter-spacing:.25pt'>al.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Chart.</span><span
lang=EN-US> </span><span lang=EN-US>Livon.</span><span lang=EN-US> </span><span
lang=EN-US>A</span><span lang=EN-US> </span><span lang=EN-US>103</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>135,3</span><span lang=EN-US> </span><span lang=EN-US>pagani</span><span
lang=EN-US> </span><span lang=EN-US>de</span><span lang=EN-US> </span><span
lang=EN-US>Curonia,</span><span lang=EN-US> </span><span lang=EN-US>de</span><span
lang=EN-US> </span><span lang=EN-US>terris</span><span lang=EN-US> </span><span
lang=EN-US>Esestua</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>kili‑<u><span style='display:none'>gund</span></u>is,</span><span
lang=EN-US> </span><span lang=EN-US>quarum</span><span lang=EN-US> </span><span
lang=EN-US>haec</span><span lang=EN-US> </span><span lang=EN-US>sunt</span><span
lang=EN-US> </span><span lang=EN-US>nomina<span style='letter-spacing:-1.75pt'>:</span></span><span
lang=EN-US> </span><span lang=EN-US>Thargolara,</span><span lang=EN-US> </span><span
lang=EN-US>Osua,</span><span lang=EN-US> </span><span lang=EN-US>Langis</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>eqs</span></i><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>135,7</span><span lang=EN-US> </span><span
lang=EN-US>de</span><span lang=EN-US> </span><span lang=EN-US>aliis</span><span
lang=EN-US> </span><span lang=EN-US>kili‑<u><span style='display:none'>gund</span></u>is,</span><span
lang=EN-US> </span><span lang=EN-US>villis</span><span lang=EN-US> </span><span
lang=EN-US>ex</span><span lang=EN-US> </span><span lang=EN-US>utraque</span><span
lang=EN-US> </span><span lang=EN-US>parte</span><span lang=EN-US> </span><span
lang=EN-US>Winda</span><span lang=EN-US> </span><span lang=EN-US>sitis.</span><span
lang=EN-US> </span><span lang=EN-US>add.</span><span lang=EN-US> </span><span
lang=EN-US>156</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>27,34</span><span lang=EN-US> </span><span
lang=EN-US>ut</span><span lang=EN-US> </span><span lang=EN-US style='letter-spacing:
2.25pt'>..</span><span lang=EN-US>.</span><span lang=EN-US> </span><span
lang=EN-US>fratres</span><span lang=EN-US> </span><span lang=EN-US>ex</span><span
lang=EN-US> </span><span lang=EN-US>donatione</span><span lang=EN-US> </span><span
lang=EN-US>nostra</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>(sc.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>episcopi)</span></i><span lang=EN-US> </span><span lang=EN-US>quartam</span><span
lang=EN-US> </span><span lang=EN-US>habeant</span><span lang=EN-US> </span><span
lang=EN-US>partem</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>Maritima,</span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>septem</span><span
lang=EN-US> </span><span lang=EN-US>scilicet</span><span lang=EN-US> </span><span
lang=EN-US>k<a name="kavenn19m_2"></a>yli‑<u><span style='display:none'>gund</span></u>is,</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>quinquaginta</span><span lang=EN-US> </span><span lang=EN-US>uncos</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>Maritima</span><span lang=EN-US> </span><span lang=EN-US>vel</span><span
lang=EN-US> </span><span lang=EN-US>Osilia.</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>ibid.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>al</span></i><span lang=EN-US>.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kilis</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>coelis.[VERWEIS]<span style='font-size:
6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kilosus</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>chylosus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kilstrio</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>gilstrio.[VERWEIS]<b>kimba</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cymba.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>[kimbema</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>symbama.<b>]</b>[VERWEIS]<b>[kimbiles</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>cimbix.<b>]</b></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>[kimbi</span></b><b><span
lang=EN-US> </span></b><b><span lang=EN-US>noxistae</span></b><span lang=EN-US>
</span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span style='font-family:Symbol;position:relative;
top:-1.0pt'>*</span><span lang=EN-US>cyminopristes.<b>]</b></span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>1.</span></b><b><span
lang=EN-US> </span></b><span style='font-size:6.0pt;font-family:Wingdings;
position:relative;top:-2.0pt'></span><b><span lang=EN-US>kimia</span></b><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><span style='font-family:Symbol;position:relative;
top:-1.0pt'>*</span><span lang=EN-US>alchimia.</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>I.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>436,33sqq.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(de</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>re</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>J.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>R<a
name="kavenn8m_1"></a>uska,</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>QuellStudGeschNat.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>5.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>1936.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>285)</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Ioh.</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span>sacerd. 174 p. 221,1sq. argentum de partibus <span
style='font-variant:small-caps;letter-spacing:.5pt'>viii</span> partes <span
style='font-variant:small-caps;letter-spacing:.5pt'>iii</span>, eris usti partes
<span style='font-variant:small-caps;letter-spacing:.5pt'>ii</span>, chibrith dianic
funde et desuper mitte; es ustum, plumbum, deinde sulphur, et dimitte super focum
multum, donec insimul liquescat et fundatur; refrigera<i><span
style='letter-spacing:.25pt'> </span></i>et erit k<a name="kavenn7m_1"></a>imium;
deinde accipe auri pars <span style='font-variant:small-caps;letter-spacing:
.5pt'>i</span>, fede pars <span style='font-variant:small-caps;letter-spacing:
.5pt'>i</span>, funde insimul et adde de kimis <i><span style='letter-spacing:
.25pt'>(ed.,</span></i><i><span style='letter-spacing:.25pt'> </span></i>kimia <i><span
style='letter-spacing:.25pt'>J.</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>Ruska,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>op.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>cit.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>285)</span></i>
pars <span style='font-variant:small-caps;letter-spacing:.5pt'>i</span>, exit aurum
optimum.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>2.</b><b> </b><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kimia</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>kinna.[VERWEIS]<b>kimiliarcha</b> <i><span
style='letter-spacing:.25pt'>sim.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span></i>cimel‑.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kimium</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>alchimia.</span><span lang=EN-US>[MFSP]</span><i><span lang=EN-US
style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>I.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>436,33sqq.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>(de</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>re</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span
style='letter-spacing:-1.5pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>2545</span><span
style='letter-spacing:-1.5pt'>,</span></i><i><span style='letter-spacing:-1.5pt'>
</span><span style='letter-spacing:.25pt'>70sqq.)</span><span style='letter-spacing:
-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>v.</span></i><i><span style='letter-spacing:.25pt'>
</span></i><i><span style='letter-spacing:.25pt'>l</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>2</span></i>.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kinna</b><b> </b>(kimia),
‑ae <i><span style='letter-spacing:.25pt'>f.</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>(arab.</span></i> qinn<span style='font-family:
"Cambria",serif'>ī</span>ya; <i><span style='letter-spacing:.25pt'>cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>A.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Siggel,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Arab.-dt.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Wb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>99</span></i><i><span
style='font-size:7.0pt;position:relative;top:-2.0pt;letter-spacing:.25pt'>b</span><span
style='letter-spacing:.25pt'>)</span></i>[MFSP]<i><span style='letter-spacing:
.25pt'>script.</span><span style='letter-spacing:-1.75pt'>:</span></i>[MFSP]simia<span
style='letter-spacing:-1.75pt'>:</span> <i><span
style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>15</span></i>.[MFSP]chemia<span
style='letter-spacing:-1.75pt'>:</span> <i><span
style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>23</span></i>.[MFSP]chimia<span
style='letter-spacing:-1.75pt'>:</span> <i><span style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>18</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>20</span></i>.[MFSP]chimea<span
style='letter-spacing:-1.75pt'>:</span> <i><span
style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>19</span></i>.<span
style='font-size:8.0pt'>[MFSP]</span>chimin(a)<span style='letter-spacing:-1.75pt'>:</span>
<i><span style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>18</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>20</span></i>.[MFSP]kim(i)n(a)<span
style='letter-spacing:-1.75pt'>:</span> <i><span style='letter-spacing:.25pt'>l</span><span style='letter-spacing:-.75pt'>.</span></i><i><span
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>19</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>20</span></i>.</p>

<p class=MsoNormal style='text-indent:6.5pt'><i><span style='letter-spacing:
.25pt'>de</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>genere</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>vasis</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>in</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>arte</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>alchemica</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>usitato</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>i.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ampulla</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>magna</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>rotunda</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>praecipue</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>ad</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>descensionem</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>d.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>apta</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>große,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>runde,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>besonders</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>zur</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>sog.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Deszension</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>geeignete</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>Flasche</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Anon.</span><span
lang=EN-US> </span><span lang=EN-US>secret.</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>82,1</span><span
lang=EN-US> </span><span lang=EN-US>s<a name="kavenn9m_1"></a>imia</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(cod.,</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>fort.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US>kimia</span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>ci.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ed.)</span></i><span lang=EN-US> </span><span lang=EN-US>est</span><span
lang=EN-US> </span><span lang=EN-US>vas</span><span lang=EN-US> </span><span
lang=EN-US>factum</span><span lang=EN-US> </span><span lang=EN-US>de</span><span
lang=EN-US> </span><span lang=EN-US>creta</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(v.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>comm.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>ed.)</span></i><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Ps.</span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Arist.</span><span lang=EN-US> </span><span lang=EN-US>magist.</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>655</span><span lang=EN-US style='font-size:7.0pt;position:relative;
top:-2.0pt'>a</span><span lang=EN-US>,45</span><span lang=EN-US> </span><span
lang=EN-US>fac</span><span lang=EN-US> </span><span lang=EN-US>ipsum</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>lapidem)</span></i><span lang=EN-US> </span><span
lang=EN-US>descendere</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>kimiam.</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Geber</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>summ.</span><span
lang=EN-US> </span><span lang=EN-US>45</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>403</span><span
lang=EN-US> </span><span lang=EN-US>quod</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(vas)</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US>vocatur</span><span
lang=EN-US> </span><span lang=EN-US>descensorium</span><span lang=EN-US> </span><span
lang=EN-US>vel</span><span lang=EN-US> </span><span lang=EN-US>c<a
name="kavenn10m_1"></a>himina</span><span lang=EN-US> </span><span lang=EN-US>(c<a
name="kavenn11m_1"></a>himia,</span><span lang=EN-US> </span><span lang=EN-US>c<a
name="kavenn12m_1"></a>himea,</span><span lang=EN-US> </span><span lang=EN-US>k<a
name="kavenn13m_1"></a>im(i)na</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>var.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>l.</span></i><span lang=EN-US>).</span><span lang=EN-US> </span><span
lang=EN-US>46</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>408</span><span lang=EN-US> </span><span
lang=EN-US>quedam</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>(sc.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>distillatio</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>est)</span></i><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>per</span><span lang=EN-US> </span><span
lang=EN-US>descensum</span><span lang=EN-US> </span><span lang=EN-US>c<a
name="kavenn10m_2"></a>himine</span><span lang=EN-US> </span><span lang=EN-US>(in</span><span
lang=EN-US> </span><span lang=EN-US>c<a name="kavenn11m_2"></a>himia<i><span
style='letter-spacing:.25pt'>,</span></i></span><span lang=EN-US> </span><span
lang=EN-US>in</span><span lang=EN-US> </span><span lang=EN-US>k<a
name="kavenn13m_2"></a>iminam,</span><span lang=EN-US> </span><span lang=EN-US>kimie</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>var.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>l.</span></i><span lang=EN-US>;</span><span
lang=EN-US> </span><span lang=EN-US>qua</span><span lang=EN-US> </span><span
lang=EN-US>mediante</span><span lang=EN-US> </span><span lang=EN-US>oleum</span><span
lang=EN-US> </span><span lang=EN-US>ex</span><span lang=EN-US> </span><span
lang=EN-US>vegetabilibus</span><span lang=EN-US> </span><span lang=EN-US>elicitur</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>add.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>pars</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>codd.</span></i><span lang=EN-US>).</span><span lang=EN-US> </span><span
lang=EN-US>forn.</span><span lang=EN-US> </span><span lang=EN-US>20</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>755</span><span lang=EN-US> </span><span lang=EN-US>quod</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>confectionis)</span></i><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>remansit</span><span lang=EN-US> </span><span
lang=EN-US>spissum</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>c<a name="kavenn14m_1"></a>hemia</span><span
lang=EN-US> </span><span lang=EN-US>bene</span><span lang=EN-US> </span><span
lang=EN-US>sigillatum</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>eqs.</span></i><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>al.</span></i></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kinoteta</span></b><b><span
lang=EN-US> </span></b><i><span lang=EN-US style='letter-spacing:.25pt'>sim.</span></i><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>coenoteta.</span><span lang=EN-US>[VERWEIS]</span><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kirica</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>kyrica.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kirion</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>cerium.</span><span lang=EN-US>[VERWEIS]</span><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kirios,</span></b><b><span lang=EN-US> </span></b><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kirius</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><span style='font-family:Symbol;position:relative;
top:-1.0pt'>*</span><span lang=EN-US>kyrius.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kis(s)eris</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>ciseris.</span><span lang=EN-US>[VERWEIS]</span><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kitonites</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>sim.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>v.</span></i><span lang=EN-US> </span><span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span><span lang=EN-US>coetonites.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kitta</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cita.[MFSP]<i><span style='letter-spacing:
.25pt'>adde</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>ad</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>vol.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>II.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>645,4sqq.</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Chart.</span>
<span lang=EN-US>Sil.</span><span lang=EN-US> </span><span lang=EN-US>D</span><span
lang=EN-US> </span><span lang=EN-US>IV</span><span lang=EN-US> </span><span
lang=EN-US>276</span><span lang=EN-US> </span><span lang=EN-US>(a.</span><span
lang=EN-US> </span><span lang=EN-US>1276)</span><span lang=EN-US> </span><span
lang=EN-US>quilibet</span><span lang=EN-US> </span><span lang=EN-US>k<a
name="kavenn15m_1"></a>meto</span><span lang=EN-US> </span><span lang=EN-US>praescriptarum</span><span
lang=EN-US> </span><span lang=EN-US>villarum</span><span lang=EN-US> </span><span
lang=EN-US>ad</span><span lang=EN-US> </span><span lang=EN-US>festum</span><span
lang=EN-US> </span><span lang=EN-US>sancti</span><span lang=EN-US> </span><span
lang=EN-US>Martini</span><span lang=EN-US> </span><span lang=EN-US>duas</span><span
lang=EN-US> </span><span lang=EN-US>kittas</span><span lang=EN-US> </span><span
lang=EN-US>canapi</span><span lang=EN-US> </span><span lang=EN-US>mundi</span><span
lang=EN-US> </span><span lang=EN-US>ratione</span><span lang=EN-US> </span><span
lang=EN-US>decimae</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>persolvere</span><span lang=EN-US> </span><span
lang=EN-US>tenetur.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kliotetra</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>cliothedrum.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kmet(h)o</span></b><span lang=EN-US> </span><span lang=EN-US>(qm‑,</span><span
lang=EN-US> </span><span lang=EN-US>kem‑,</span><span lang=EN-US> </span><span
lang=EN-US>kym‑),</span><span lang=EN-US> </span><span lang=EN-US>‑onis</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>m.</span></i><span
lang=EN-US>[MFSP]</span><span lang=EN-US>(<i><span style='letter-spacing:.25pt'>polon.</span></i></span><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US>kmie</span><span
lang=EN-US style='font-family:"Stpl_ Garamond_ Akzente",serif'>ç</span><span
lang=EN-US>;</span><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>cf.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Lex.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Polon.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>s.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>v.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US>cmetho)</span><span
lang=EN-US>[MFSP]</span><i><span lang=EN-US style='letter-spacing:.25pt'>colonus,</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>rusticus</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>–</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Siedler,</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Bauer</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Chart</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>Sil.</span><span
lang=EN-US> </span><span lang=EN-US>D</span><span lang=EN-US> </span><span
lang=EN-US>III</span><span lang=EN-US> </span><span lang=EN-US>47</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>42,24</span><span lang=EN-US> </span><span lang=EN-US>(a.</span><span
lang=EN-US> </span><span lang=EN-US>1252)</span><span lang=EN-US> </span><span
lang=EN-US>habuit</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>dux</span></i><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>quandam</span><span lang=EN-US> </span><span
lang=EN-US>sortem,</span><span lang=EN-US> </span><span lang=EN-US>que</span><span
lang=EN-US> </span><span lang=EN-US>vocatur</span><span lang=EN-US> </span><span
lang=EN-US>Lang,</span><span lang=EN-US> </span><span lang=EN-US>que</span><span
lang=EN-US> </span><span lang=EN-US>est</span><span lang=EN-US> </span><span
lang=EN-US>sita</span><span lang=EN-US> </span><span lang=EN-US>super</span><span
lang=EN-US> </span><span lang=EN-US>Vartam</span><span lang=EN-US> </span><span
lang=EN-US>fluvium,</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>qua</span><span lang=EN-US> </span><span
lang=EN-US>ex</span><span lang=EN-US> </span><span lang=EN-US>antico</span><span
lang=EN-US> </span><span lang=EN-US>erant</span><span lang=EN-US> </span><span
lang=EN-US>duo</span><span lang=EN-US> </span><span lang=EN-US>kemetones</span><span
lang=EN-US> </span><span lang=EN-US>proprii</span><span lang=EN-US> </span><span
lang=EN-US>patris</span><span lang=EN-US> </span><span lang=EN-US>nostri</span><span
lang=EN-US> </span><span lang=EN-US>venatores</span><span lang=EN-US> </span><span
lang=EN-US>castorum.</span><span lang=EN-US> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Chart.</span><span
lang=EN-US> </span><span lang=EN-US>Pommerell.</span><span lang=EN-US> </span><span
lang=EN-US>209</span><span lang=EN-US> </span><span lang=EN-US>abbati</span><span
lang=EN-US> </span><span lang=EN-US>et</span><span lang=EN-US> </span><span
lang=EN-US>conventui</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>concedimus</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>dux)</span></i><span lang=EN-US>,</span><span lang=EN-US> </span><span
lang=EN-US>ut</span><span lang=EN-US> </span><span lang=EN-US>ky‑<u><span
style='display:none'>met</span></u>hones</span><span lang=EN-US> </span><span
lang=EN-US>eorum</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>ab</span><span lang=EN-US> </span><span
lang=EN-US>omni</span><span lang=EN-US> </span><span lang=EN-US>exactione</span><span
lang=EN-US> </span><span lang=EN-US>nostri</span><span lang=EN-US> </span><span
lang=EN-US>servicii</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>plenam</span><span lang=EN-US> </span><span
lang=EN-US>inperpetuum</span><span lang=EN-US> </span><span lang=EN-US>possideant</span><span
lang=EN-US> </span><span lang=EN-US>libertatem.</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Chart</span><span
lang=EN-US>.</span><span lang=EN-US> </span><span lang=EN-US>Sil.</span><span
lang=EN-US> </span><span lang=EN-US>D</span><span lang=EN-US> </span><span
lang=EN-US>IV</span><span lang=EN-US> </span><span lang=EN-US>276</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kme</span></u>tones.</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Chart.</span><span lang=EN-US> </span><span lang=EN-US>Pommerell.</span><span
lang=EN-US> </span><span lang=EN-US>320</span><span lang=EN-US> </span><span
lang=EN-US>(a.</span><span lang=EN-US> </span><span lang=EN-US>1280)</span><span
lang=EN-US> </span><span lang=EN-US>addidit</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>dux</span></i><span lang=EN-US> </span><span
lang=EN-US>eciam</span><span lang=EN-US> </span><span lang=EN-US>lacus</span><span
lang=EN-US> </span><span lang=EN-US>suos</span><span lang=EN-US> </span><span
lang=EN-US>omnes</span><span lang=EN-US> </span><span lang=EN-US>ibidem</span><span
lang=EN-US> </span><span lang=EN-US>eidem</span><span lang=EN-US> </span><span
lang=EN-US>domui</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>iure</span><span lang=EN-US> </span><span
lang=EN-US>perpetuo</span><span lang=EN-US> </span><span lang=EN-US>sine</span><span
lang=EN-US> </span><span lang=EN-US>omni</span><span lang=EN-US> </span><span
lang=EN-US>participatione</span><span lang=EN-US> </span><span lang=EN-US>circumsedencium</span><span
lang=EN-US> </span><span lang=EN-US>militum</span><span lang=EN-US> </span><span
lang=EN-US>vel</span><span lang=EN-US> </span><span lang=EN-US>qmetonum</span><span
lang=EN-US> </span><span lang=EN-US>(‑<u><span style='display:none'>kme</span></u>tonum</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>K</span></i><span
lang=EN-US>).</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>et</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>l</span></i><i><span lang=EN-US
style='letter-spacing:-.75pt'>.</span></i><i><span lang=EN-US style='letter-spacing:
-1.75pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>28</span></i><span
lang=EN-US>.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>koga</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cocca.[VERWEIS]<span style='font-size:
6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kogge(n)mester</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>coggemester.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kokemester</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cokemester.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kokko</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cocca.[VERWEIS]<b>koky</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> coccyx.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>komarcos</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>comarchus.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>konversus</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>v.</span></i><span
lang=EN-US> </span><span lang=EN-US>converto.</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>adde</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ad</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>vol.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>II.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>p.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>1838,10sqq.</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Chart.</span><span lang=EN-US> </span><span lang=EN-US>Slag.</span><span
lang=EN-US> </span><span lang=EN-US>26</span><span lang=EN-US> </span><span
lang=EN-US>(a.</span><span lang=EN-US> </span><span lang=EN-US>1276)</span><span
lang=EN-US> </span><span lang=EN-US>fratres</span><span lang=EN-US> </span><span
lang=EN-US>Walchunus,</span><span lang=EN-US> </span><span lang=EN-US>Wernherus,</span><span
lang=EN-US> </span><span lang=EN-US>Fridericus</span><span lang=EN-US> </span><span
lang=EN-US>k‑<u><span style='display:none'>onvers</span></u>i</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(v.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>notam</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ed.)</span></i><span lang=EN-US>.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kora</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cora.[VERWEIS]<b>koram</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> coram.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>koremede</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>curmeda.[VERWEIS]<b>koriletum</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> coryletum.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>koropalates</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> curopalates.[VERWEIS]<b>kosmus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cosmos.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kota</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cota.[VERWEIS]<span style='font-size:
6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kottus</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> 1. <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>cottus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>koufmannus</b> (kufmanus),
‑i <i><span style='letter-spacing:.25pt'>m.</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>(theod.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>vet.</span></i><i><span
style='letter-spacing:.25pt'> </span></i>koufman; <i><span style='letter-spacing:
.25pt'>cf.</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>Lexer,</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>Mittelhochdt.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Handwb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>I.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>1696)</span></i>[MFSP]<i><span
style='letter-spacing:.25pt'>mercator</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‘Kaufmann’</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Chart</span>.
scrin. Col. A II 2 p. 17,10 (a. 1135/80) Herbort, kufmani amicus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kozzus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cozzus.[VERWEIS]<span style='font-size:
6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kromios</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>crom(m)yon.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kronius</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> chronius.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>ktisma</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>ctisma.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kufmanus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>koufmannus.[VERWEIS]<span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kufoides</b>
<i><span style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:
Symbol;position:relative;top:-1.0pt'>*</span>cyphoides.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>kuneus</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cuneus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><span class=lemma>kungelinus</span><b>,</b>
‑a, ‑um.[MFSP]<i><span style='letter-spacing:.25pt'>(theod.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>vet.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>kuniclin;</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>cf.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Lexer,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Mittelhochdt.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Handwb.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>I.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>p.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>1775</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>s.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>v.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><span style='font-size:7.0pt;
position:relative;top:-2.0pt'>2</span>küniclin<i><span style='letter-spacing:
.25pt'>)</span></i><i><span style='letter-spacing:.25pt'>[MFSP]</span><span
style='letter-spacing:.25pt'>qui</span></i><i><span style='letter-spacing:.25pt'>
</span><span style='letter-spacing:.25pt'>cuniculi</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>est,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>leporinus</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Kaninchen‑</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Trad.</span>
Weiss. app. II 7 p. 329,4 (a. 1265) quod pellifices in omni suo opere veteres pelles
novis ‑<u><span style='display:none'>kungelin</span></u>um <i><span
style='letter-spacing:.25pt'>(fort.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>subest</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>glossa)</span></i><i><span
style='letter-spacing:.25pt'> </span></i>leporinis non coniungent.[VERWEIS]<i><span
style='letter-spacing:.25pt'>cf.</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-family:Symbol;position:relative;top:-1.0pt'>*</span>cuniculinus.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kurmeda</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>curmeda.[VERWEIS]<b>kurro</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. curro.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kurtis</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> 1. <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cortis.[VERWEIS]<b>kyan‑</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cyan‑.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kylis</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>coelis.[VERWEIS]<b>kylos</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> chylus.[VERWEIS]<b>kymba</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cymba.</p>

<p class=MsoNormal style='text-indent:6.5pt'><b>[kymbos</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>cephen.<b>]</b>[VERWEIS]<b>kymera</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> chimaera.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kymetho</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>kmet(h)o.[VERWEIS]<b>kypseli</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> cypsele.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b>kyrias</b> <i><span
style='letter-spacing:.25pt'>v.</span></i> <span style='font-family:Symbol;
position:relative;top:-1.0pt'>*</span>kyrius.</p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><span class=lemma>kyrica</span>
(kir‑, kyrr<span style='font-size:8.0pt'>‑,</span><span style='font-size:8.0pt'>
</span><span style='font-size:8.0pt'>‑ia,</span><span style='font-size:8.0pt'> </span><span
style='font-size:8.0pt'>‑cha)</span>, ‑ae <i><span style='letter-spacing:.25pt'>f.</span></i>[MFSP](*<span
style='font-family:OldGreekSerif;letter-spacing:.25pt'>kurikë</span>, <i><span
style='letter-spacing:.25pt'>theod.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>vet.</span></i><i><span
style='letter-spacing:.25pt'> </span></i>kirihha; <i><span style='letter-spacing:
.25pt'>cf.</span></i><i><span style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>Stotz,</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>Handb.</span></i><i><span
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>1,IV</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>§</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>9.4</span></i><span lang=EN-US>)</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>domus</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Domini,</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Dei</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>–</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Haus</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>des</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Herrn,</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Gotteshaus,</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>‘Kirche’</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>(fere</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>proprie</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>de</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>aedificio;</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>translate</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>de</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>institutione</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>l</span></i><i><span lang=EN-US
style='letter-spacing:-.75pt'>.</span></i><i><span lang=EN-US style='letter-spacing:
-1.75pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>12)</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Amalar.</span><span lang=EN-US> </span><span
lang=EN-US>off.</span><span lang=EN-US> </span><span lang=EN-US>3,2,1</span><span
lang=EN-US> </span><span lang=EN-US>ipsa</span><span lang=EN-US> </span><span
lang=EN-US>domus</span><span lang=EN-US> </span><span lang=EN-US>vocatur</span><span
lang=EN-US> </span><span lang=EN-US>ecclesia,</span><span lang=EN-US> </span><span
lang=EN-US>quia</span><span lang=EN-US> </span><span lang=EN-US>ecclesiam</span><span
lang=EN-US> </span><span lang=EN-US>continet;</span><span lang=EN-US> </span><span
lang=EN-US>ipsa</span><span lang=EN-US> </span><span lang=EN-US>vocatur</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kyric</span></u>a</span><span
lang=EN-US> </span><span lang=EN-US>(kyrrica</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>P3</span></i><span lang=EN-US>),</span><span
lang=EN-US> </span><span lang=EN-US>quia</span><span lang=EN-US> </span><span
lang=EN-US>est</span><span lang=EN-US> </span><span lang=EN-US>dominicalis<span
style='letter-spacing:-1.75pt'>:</span></span><span lang=EN-US> </span><span
lang=EN-US>kyrius</span><span lang=EN-US> </span><span lang=EN-US>grece,</span><span
lang=EN-US> </span><span lang=EN-US>latine</span><span lang=EN-US> </span><span
lang=EN-US>dominus,</span><span lang=EN-US> </span><span lang=EN-US>ac</span><span
lang=EN-US> </span><span lang=EN-US>ideo</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kyric</span></u>a</span><span
lang=EN-US> </span><span lang=EN-US>(kyria</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>A</span></i><span lang=EN-US>),</span><span
lang=EN-US> </span><span lang=EN-US>dominicalis</span><span lang=EN-US> </span><span
lang=EN-US>(<i><span style='letter-spacing:.25pt'>item</span></i></span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Honor.</span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>August.</span><span lang=EN-US> </span><span lang=EN-US>sacram.</span><span
lang=EN-US> </span><span lang=EN-US>31).</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Walahfr.</span><span
lang=EN-US> </span><span lang=EN-US>exord.</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>481,29</span><span
lang=EN-US>  </span><span lang=EN-US>‑<u><span style='display:none'>kyric</span></u>a</span><span
lang=EN-US> </span><span lang=EN-US>(ki‑<u><span style='display:none'>rica</span></u></span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>45</span></i><span
lang=EN-US>).</span><span lang=EN-US> </span><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Wolfher.</span><span lang=EN-US> </span><span
lang=EN-US>Godeh.</span><span lang=EN-US> </span><span lang=EN-US>I</span><span
lang=EN-US> </span><span lang=EN-US>13</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>178,8</span><span
lang=EN-US> </span><span lang=EN-US>ki‑<u><span style='display:none'>ric</span></u>as</span><span
lang=EN-US> </span><span lang=EN-US>(kirias</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>1</span></i><span lang=EN-US>)</span><span
lang=EN-US> </span><span lang=EN-US>plures</span><span lang=EN-US> </span><span
lang=EN-US style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>construxit.</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Donizo</span><span
lang=EN-US> </span><span lang=EN-US>Mathild.</span><span lang=EN-US> </span><span
lang=EN-US>1,651</span><span lang=EN-US> </span><span lang=EN-US>libera</span><span
lang=EN-US> </span><span lang=EN-US>per</span><span lang=EN-US> </span><span
lang=EN-US>papam</span><span lang=EN-US> </span><span lang=EN-US>mea</span><span
lang=EN-US> </span><span lang=EN-US>k<a name="kavenn16m_1"></a>yrrica</span><span
lang=EN-US> </span><span lang=EN-US>(gloss.<span style='letter-spacing:-1.75pt'>:</span></span><span
lang=EN-US> </span><span lang=EN-US>i.</span><span lang=EN-US> </span><span
lang=EN-US>e.</span><span lang=EN-US> </span><span lang=EN-US>ecclesia)</span><span
lang=EN-US> </span><span lang=EN-US>permanet</span><span lang=EN-US> </span><span
lang=EN-US>alma.</span><span lang=EN-US> </span><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Honor.</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>August.</span><span
lang=EN-US> </span><span lang=EN-US>spec.</span><span lang=EN-US> </span><span
lang=EN-US>add.</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>9,24</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kyri</span></u>cha.</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>al.</span></i></p>

<p class=MsoNormal style='text-indent:6.5pt'><b><span lang=EN-US>kyrieleison</span></b><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>sim.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><span style='font-family:Symbol;position:relative;
top:-1.0pt'>*</span><span lang=EN-US>kyrius.</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kyrieleizo</span></b><span lang=EN-US> </span><span lang=EN-US>(cy‑),</span><span
lang=EN-US> </span><span lang=EN-US>‑are.</span><span lang=EN-US>[MFSP]</span><span
lang=EN-US>(kyrieleison;</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>cf.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Stotz,</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Handb.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>2,VI</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>§</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>104.7</span></i>)[MFSP]<i><span
style='letter-spacing:.25pt'>carmen</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>sacrum</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‘Kyrieeleison’</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>d.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dicere,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>cantare</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>das</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>‘Kyrieeleison’</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>genannte</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Gebet</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>sprechen,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>singen</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Hugeb.</span>
<span lang=EN-US>Wynneb.</span><span lang=EN-US> </span><span lang=EN-US>13</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>117,2</span><span lang=EN-US> </span><span lang=EN-US>omnis</span><span
lang=EN-US> </span><span lang=EN-US>plebs</span><span lang=EN-US> </span><span
lang=EN-US>comitantes</span><span lang=EN-US> </span><span lang=EN-US>cy‑<u><span
style='display:none'>rieleiza</span></u>bant</span><span lang=EN-US> </span><span
lang=EN-US>(k‑<u><span style='display:none'>yrieleiza</span></u>bant</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>2,</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>4,</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>4</span></i><i><span
lang=EN-US style='font-size:7.0pt;position:relative;top:-2.0pt;letter-spacing:
.25pt'>b</span></i><span lang=EN-US>).</span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><span class=lemma><span
lang=EN-US>kyrius</span></span><span lang=EN-US> </span><span lang=EN-US>(kir‑,</span><span
lang=EN-US> </span><span lang=EN-US>‑rr‑),</span><span lang=EN-US> </span><span
lang=EN-US>‑i</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>m.</span></i><span lang=EN-US>[MFSP]</span><span
lang=EN-US>(</span><span lang=EN-US style='font-family:OldGreekSerif;
letter-spacing:.25pt'>kúrioß</span><span lang=EN-US>)</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>script.</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US>[MFSP]</span><span
lang=EN-US>quir‑</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>sim.</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><i><span style='letter-spacing:-1.5pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>p.</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>2548</span></i><i><span lang=EN-US
style='letter-spacing:-1.5pt'>,</span></i><i><span lang=EN-US style='letter-spacing:
-1.5pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>8</span></i><span
lang=EN-US>.</span><span lang=EN-US>[MFSP]</span><i><span lang=EN-US
style='letter-spacing:.7pt'>?</span></i><span lang=EN-US>gir‑<span
style='letter-spacing:-1.75pt'>:</span></span><span lang=EN-US> </span><i><span style='letter-spacing:-1.5pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>p.</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>2548</span></i><i><span lang=EN-US
style='letter-spacing:-1.5pt'>,</span></i><i><span lang=EN-US style='letter-spacing:
-1.5pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>24</span></i><span
lang=EN-US>.</span><span lang=EN-US>[MFSP]</span><i><span lang=EN-US
style='letter-spacing:.25pt'>form.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='font-size:
9.0pt;letter-spacing:.25pt'>voc.</span></i><i><span lang=EN-US
style='font-size:9.0pt;letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='font-size:9.0pt;letter-spacing:.25pt'>vel</span></i><i><span lang=EN-US
style='font-size:9.0pt;letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='font-size:9.0pt;letter-spacing:.25pt'>nom.</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US>[MFSP]</span><span
lang=EN-US>‑os<span style='letter-spacing:-1.75pt'>:</span></span><span
lang=EN-US> </span><i><span style='letter-spacing:-1.5pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>p.</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>2548</span></i><i><span lang=EN-US
style='letter-spacing:-1.5pt'>,</span></i><i><span lang=EN-US style='letter-spacing:
-1.5pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>3</span></i><i><span
lang=EN-US style='letter-spacing:-.75pt'>.</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'> </span><span style='letter-spacing:.25pt'>20</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>23</span><span style='letter-spacing:
-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'> </span><span
style='letter-spacing:.25pt'>26</span></i>.[MFSP]‑as<span style='letter-spacing:
-1.75pt'>:</span> <i><span style='letter-spacing:.25pt'>l</span><span
style='letter-spacing:-.75pt'>.</span></i><i><span style='letter-spacing:-1.75pt'>
</span><span style='letter-spacing:.25pt'>25</span></i>.</p>

<p class=MsoNormal style='text-indent:6.5pt'><i><span lang=EN-US
style='letter-spacing:.25pt'>dominus</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>–</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>Herr</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US>[MFSP]</span><b><span
lang=EN-US>1</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>de</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>Deo,</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>Christo</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US>[MFSP]</span><b><span
lang=EN-US>a</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>in</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>univ.</span></i><i><span
lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><span lang=EN-US style='font-variant:
small-caps;letter-spacing:.5pt'>Hymn.</span><span lang=EN-US> </span><span
lang=EN-US>abeced.</span><span lang=EN-US> </span><span lang=EN-US>K</span><span
lang=EN-US> </span><span lang=EN-US>1</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kyri</span></u>a<a name="kavenn3m_1"></a>s,</span><span
lang=EN-US> </span><span lang=EN-US>culmen,</span><span lang=EN-US> </span><span
lang=EN-US>creator</span><span lang=EN-US> </span><span lang=EN-US>celse</span><span
lang=EN-US> </span><span lang=EN-US>celicorum</span><span lang=EN-US> </span><span
lang=EN-US>lexque</span><span lang=EN-US> </span><span lang=EN-US>rerum,</span><span
lang=EN-US> </span><span lang=EN-US>ominum</span><span lang=EN-US> </span><span
lang=EN-US>et</span><span lang=EN-US> </span><span lang=EN-US>angelorum</span><span
lang=EN-US> </span><i><span lang=EN-US style='letter-spacing:.25pt'>(v.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>comm.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>ed.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>p.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>84)</span></i><span lang=EN-US>.</span><span lang=EN-US> </span><span
style='font-variant:small-caps;letter-spacing:.5pt'>Rhythm.</span> 81,17,5 terra
tremescit c<span style='font-family:"Cambria",serif'>ę</span>lestium impetu, iudex
advenit <span style='letter-spacing:3.0pt'>homousion</span> ‑<u><span
style='display:none'>kyri</span></u>us (81,47,1. 90,1,6). <span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Hraban.</span><span
lang=EN-US> </span><span lang=EN-US>carm.</span><span lang=EN-US> </span><span
lang=EN-US>39,99,6</span><span lang=EN-US> </span><span lang=EN-US>ore,</span><span
lang=EN-US> </span><span lang=EN-US>corde</span><span lang=EN-US> </span><span
lang=EN-US>et</span><span lang=EN-US> </span><span lang=EN-US>opere</span><span
lang=EN-US> </span><span lang=EN-US>te</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(sc.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Christum)</span></i><span lang=EN-US> </span><span lang=EN-US>canam</span><span
lang=EN-US> </span><span lang=EN-US>laudem,</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kyri</span></u>e.</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Carm.</span><span lang=EN-US> </span><span lang=EN-US>Bur.</span><span
lang=EN-US> </span><span lang=EN-US>51</span><span lang=EN-US style='font-size:
7.0pt;position:relative;top:-2.0pt'>a</span><span lang=EN-US>,1,8</span><span
lang=EN-US> </span><span lang=EN-US>miserere,</span><span lang=EN-US> </span><span
lang=EN-US>‑<u><span style='display:none'>kyri</span></u>o<a name="kavenn4m_1"></a>s,</span><span
lang=EN-US> </span><span lang=EN-US>salva</span><span lang=EN-US> </span><span
lang=EN-US>tuos</span><span lang=EN-US> </span><span lang=EN-US>famulos.</span><span
lang=EN-US> </span><span lang=EN-US style='font-variant:small-caps;letter-spacing:
.5pt'>Vita</span><span lang=EN-US> </span><span lang=EN-US>Hildeg.</span><span
lang=EN-US> </span><span lang=EN-US>Bing.</span><span lang=EN-US> </span><span
lang=EN-US>I</span><span lang=EN-US> </span><span lang=EN-US>3,16</span><span
lang=EN-US> </span><span lang=EN-US>l.</span><span lang=EN-US> </span><span
lang=EN-US>34</span><span lang=EN-US> </span><span lang=EN-US>(CCCont.</span><span
lang=EN-US> </span><span lang=EN-US>Med.</span><span lang=EN-US> </span><span
lang=EN-US>CXXXI.</span><span lang=EN-US> </span><span lang=EN-US>1993.</span><span
lang=EN-US> </span><span lang=EN-US>p.</span><span lang=EN-US> </span><span
lang=EN-US>54)</span><span lang=EN-US> </span><span lang=EN-US>in</span><span
lang=EN-US> </span><span lang=EN-US>hunc</span><span lang=EN-US> </span><span
lang=EN-US>modum</span><span lang=EN-US> </span><span lang=EN-US>exposuit</span><span
lang=EN-US> </span><span lang=EN-US>litteras<span style='letter-spacing:-1.75pt'>:</span></span><span
lang=EN-US> </span><span lang=EN-US>K</span><span lang=EN-US> </span><span
lang=EN-US>kirium</span><span lang=EN-US> </span><span lang=EN-US>(‑<u><span
style='display:none'>kyri</span></u>e</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>B</span></i><span lang=EN-US>),</span><span
lang=EN-US> </span><span lang=EN-US>P</span><span lang=EN-US> </span><span
lang=EN-US>presbyter</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>eqs</span></i><span lang=EN-US>.</span><span
lang=EN-US>[MFSP]</span><b><span lang=EN-US>b</span></b><span lang=EN-US> </span><i><span
lang=EN-US style='font-size:8.0pt;letter-spacing:.25pt'>iunctura</span></i><i><span
lang=EN-US style='font-size:8.0pt;letter-spacing:.25pt'> </span></i><span
lang=EN-US>Kyrieleison</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>sim.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>i.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>q.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>carmen</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>sacrum</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>‘Kyrieeleison’</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>
</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>q.</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>d.</span></i><i><span lang=EN-US style='letter-spacing:
.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:.25pt'>–</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>das</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>‘Kyrieeleison’</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>
</span></i><i><span lang=EN-US style='letter-spacing:.25pt'>genannte</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US
style='letter-spacing:.25pt'>Gebet</span></i><i><span lang=EN-US
style='letter-spacing:-1.75pt'>:</span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Conc.</span><span
lang=EN-US> </span><span lang=EN-US>Merov.</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>56,23</span><span
lang=EN-US> </span><span lang=EN-US>ut</span><span lang=EN-US> </span><span
lang=EN-US>Q<a name="kavenn17m_1"></a>uirieleison</span><span lang=EN-US> </span><span
lang=EN-US>(Quiriaeleison,</span><span lang=EN-US> </span><span lang=EN-US>Quyrieleson,</span><span
lang=EN-US> </span><span lang=EN-US>Queirie</span><span lang=EN-US> </span><span
lang=EN-US>heleison,</span><span lang=EN-US> </span><span lang=EN-US>K‑<u><span
style='display:none'>yri</span></u>eleison,</span><span lang=EN-US> </span><span
lang=EN-US>Kirieleison</span><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>var.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>l.</span></i><span lang=EN-US>)</span><span lang=EN-US> </span><span
lang=EN-US>frequentius</span><span lang=EN-US> </span><span lang=EN-US
style='letter-spacing:2.25pt'>..</span><span lang=EN-US>.</span><span
lang=EN-US> </span><span lang=EN-US>dicatur.</span><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Epist.</span><span
lang=EN-US> </span><span lang=EN-US>var.</span><span lang=EN-US> </span>II 4,7 ut
finitis cursibus incoepturi K‑<u><span style='display:none'>yri</span></u>eleison
(Kyrr‑<u><span style='display:none'>ieleison</span></u> <i><span
style='letter-spacing:.25pt'>T</span></i>) genua flectant <i><span
style='letter-spacing:.25pt'>fratres</span></i>. <span style='font-variant:
small-caps;letter-spacing:.5pt'>Walahfr.</span> exord. 23 p. 497,17 laetaniae <span
style='letter-spacing:2.25pt'>..</span><span style='letter-spacing:1.75pt'>.</span>,
quae sequuntur, id est Kyrie (Kirie <i><span style='letter-spacing:.25pt'>var.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>l.</span></i>)
eleison et Christe eleison, a Grecorum usu sumptae creduntur.[MFSP]<i><span
style='letter-spacing:.25pt'>translate</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>i.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>q.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>infelicitas,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>miseria</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>–</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Unglück,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Jammer</span><span
style='letter-spacing:-1.75pt'>:</span></i><i><span style='letter-spacing:.25pt'>
</span></i><span style='font-variant:small-caps;letter-spacing:.5pt'>Bruno</span><span
style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
style='font-variant:small-caps;letter-spacing:.5pt'>Querf.</span> fratr. 32 p. 84,3
sibi Alleluia habuerunt <i><span style='letter-spacing:.25pt'>(sc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>iusti)</span></i>,
nobis K‑<u><span style='display:none'>yri</span></u>eleyson dimiserunt.[MFSP]<b>2</b>
<i><span style='letter-spacing:.25pt'>usu</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>communi</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>de</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>omni</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>regnante,</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>dominante</span><span
style='letter-spacing:-1.75pt'>:</span></i> <span style='font-variant:small-caps;
letter-spacing:.5pt'>Ioh.</span><span style='font-variant:small-caps;
letter-spacing:.5pt'> </span><span style='font-variant:small-caps;letter-spacing:
.5pt'>Scot.</span> carm. 8,1,1 kyrrie <i><span style='letter-spacing:.25pt'>(sc.</span></i><i><span
style='letter-spacing:.25pt'> </span><span style='letter-spacing:.25pt'>Karolus)</span></i>,
caeligenae cui pollet gratia formae <span style='letter-spacing:2.25pt'>..</span><span
style='letter-spacing:1.75pt'>.</span>, salve, Christicolum vertex, gratissime regum.
<span lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Benzo</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US>ad</span><span lang=EN-US> </span><span lang=EN-US>Heinr.</span><span
lang=EN-US> </span><span lang=EN-US>4,41</span><span lang=EN-US> </span><span
lang=EN-US>p.</span><span lang=EN-US> </span><span lang=EN-US>424,10</span><span
lang=EN-US> </span><span lang=EN-US>in</span><span lang=EN-US> </span><span
lang=EN-US>sanctis</span><span lang=EN-US> </span><span lang=EN-US>narratur</span><span
lang=EN-US> </span><span lang=EN-US>aecclesiis,</span><span lang=EN-US> </span><span
lang=EN-US>quod</span><span lang=EN-US> </span><span lang=EN-US>homo</span><span
lang=EN-US> </span><span lang=EN-US>sit</span><span lang=EN-US> </span><span
lang=EN-US>k<a name="kavenn4m_2"></a>yrrios</span><span lang=EN-US> </span><span
lang=EN-US>bestiis,</span><span lang=EN-US> </span><span lang=EN-US>utens</span><span
lang=EN-US> </span><span lang=EN-US>est</span><span lang=EN-US> </span><span
lang=EN-US>quippe</span><span lang=EN-US> </span><span lang=EN-US>rationibus,</span><span
lang=EN-US> </span><span lang=EN-US>quod</span><span lang=EN-US> </span><span
lang=EN-US>denegatum</span><span lang=EN-US> </span><span lang=EN-US>est</span><span
lang=EN-US> </span><span lang=EN-US>pecoribus</span><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>(cf.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>Vulg.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span><span
style='letter-spacing:.25pt'>Gen.</span></i><i><span style='letter-spacing:
.25pt'> </span><span style='letter-spacing:.25pt'>1,26)</span></i>. <span
style='font-variant:small-caps;letter-spacing:.5pt'>Chron.</span> Ebersh. <span
lang=EN-US>2</span><span lang=EN-US> </span><span lang=EN-US>p.</span><span
lang=EN-US> </span><span lang=EN-US>432,16</span><span lang=EN-US> </span><span
lang=EN-US>Greca</span><span lang=EN-US> </span><span lang=EN-US>etymologia</span><span
lang=EN-US> </span><span lang=EN-US>Mercurius</span><span lang=EN-US> </span><span
lang=EN-US>quasi</span><span lang=EN-US> </span><span lang=EN-US>mercatorum</span><span
lang=EN-US> </span><span lang=EN-US>k<a name="kavenn4m_4"></a>irios</span><span
lang=EN-US> </span><span lang=EN-US>vocatur.</span><span lang=EN-US>[MFSP]</span><i><span
lang=EN-US style='letter-spacing:.25pt'>fort.</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>add.</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Gesta</span><span
lang=EN-US> </span><span lang=EN-US>Apoll.</span><span lang=EN-US> </span><span
lang=EN-US>786</span><span lang=EN-US>  </span><span lang=EN-US>urbis</span><span
lang=EN-US> </span><span lang=EN-US>nunc</span><span lang=EN-US> </span><span
lang=EN-US>e</span><span lang=EN-US> </span><span lang=EN-US>g<a
name="kavenn2m_1"></a>irius</span><span lang=EN-US> </span><span lang=EN-US>non</span><span
lang=EN-US> </span><span lang=EN-US>te</span><span lang=EN-US> </span><span
lang=EN-US>felicior</span><span lang=EN-US> </span><span lang=EN-US>ullus.</span><span
lang=EN-US>[MFSP]</span><b><span lang=EN-US>3</span></b><span lang=EN-US> </span><i><span
lang=EN-US style='letter-spacing:.25pt'>per</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>compar.</span></i><i><span lang=EN-US style='letter-spacing:.25pt'> </span></i><i><span
lang=EN-US style='letter-spacing:.25pt'>de</span></i><i><span lang=EN-US
style='letter-spacing:.25pt'> </span></i><i><span lang=EN-US style='letter-spacing:
.25pt'>gustu</span></i><i><span lang=EN-US style='letter-spacing:-1.75pt'>:</span></i><i><span
lang=EN-US style='letter-spacing:.25pt'> </span></i><span lang=EN-US
style='font-variant:small-caps;letter-spacing:.5pt'>Rein.</span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'> </span><span
lang=EN-US style='font-variant:small-caps;letter-spacing:.5pt'>Alem.</span><span
lang=EN-US> </span><span lang=EN-US>phagifac.</span><span lang=EN-US> </span><span
lang=EN-US>360</span><span lang=EN-US> </span><span lang=EN-US>regna</span><span
lang=EN-US> </span><span lang=EN-US>tenet</span><span lang=EN-US> </span><span
lang=EN-US>gustus,</span><span lang=EN-US> </span><span lang=EN-US>ferclorum</span><span
lang=EN-US> </span><span lang=EN-US>‑<u><span style='display:none'>kyri</span></u>os<a
name="kavenn4m_3"></a>,</span><span lang=EN-US> </span><span lang=EN-US>ad</span><span
lang=EN-US> </span><span lang=EN-US>plus</span><span lang=EN-US> </span><span
lang=EN-US>lata</span><span lang=EN-US> </span><span lang=EN-US>tribus</span><span
lang=EN-US> </span><span lang=EN-US>digitis. <span style='color:#5B9BD5'>[EndeLemmaStreckeAutor]</span><i><span
style='letter-spacing:.25pt'>Mandrin</span></i></span></p>

<p class=MsoNormal style='text-indent:6.5pt'><span style='font-size:6.0pt;
font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kyrrica</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>kyrica.</span><span lang=EN-US>[VERWEIS]</span><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kyrrie,</span></b><b><span lang=EN-US> </span></b><span
style='font-size:6.0pt;font-family:Wingdings;position:relative;top:-2.0pt'></span><b><span
lang=EN-US>kyrrios</span></b><span lang=EN-US> </span><i><span lang=EN-US
style='letter-spacing:.25pt'>v.</span></i><span lang=EN-US> </span><span
style='font-family:Symbol;position:relative;top:-1.0pt'>*</span><span
lang=EN-US>kyrius.</span></p>

</div>

</body>

</html>
"""
