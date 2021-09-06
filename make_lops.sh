function make_lop {
    dirname=$1
    author=$2
    shift
    shift
    echo $author
    rm -rf $dirname
    mkdir $dirname
    ### IF YOU WANT TO HAVE RELEVANT PUBS FOR AKA, DO IT HERE LIKE THIS:
    #python3 personal_lop.py --latex "$author" --author $* -e -r "$FILIP_AKA_2020" > $dirname/$dirname.tex
    python3 personal_lop.py --latex "$author" --author $* -e  > $dirname/$dirname.tex
    cd $dirname
    ln -s ../turkunlp.bib .
    ln -s ../unsrtnat-nourl.bst .
    pdflatex $dirname.tex
    for a in *.aux
    do
	bibtex $a
    done
    pdflatex $dirname.tex
    pdflatex $dirname.tex
    cd ..
    echo
    echo
}

#       directory  latexname   search
FILIP_AKA_2020="pyysalo2021wikiberts,kanerva20201paraphrase,kanerva-etal-2020-turku,kanerva2020lemmatizer,kanerva2020dependency,tiedemann2020fiskmo,ronnqvist2019bert,zeman2018stoverview,udst:turkunlp,luotolahti2015parsebanks"

make_lop ginter_lop "Filip Ginter" Ginter 
#make_lop kanerva_lop "Jenna Kanerva (Nyblom)" Kanerva Nyblom
#make_lop mehryary_lop "Farrokh Mehryary" Mehryary
#make_lop luotolahti_lop "Juhani Luotolahti" Luotolahti
#make_lop pyysalo_lop "Sampo Pyysalo" Pyysalo
