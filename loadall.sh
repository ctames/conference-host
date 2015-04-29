for f in dbdata/pickle/*-institutions.pickle
do
   echo "Processing file $f"
   time python loadnsf.py $f
done

for f in dbdata/pickle/*-pis.pickle
do
   echo "Processing file $f"
   time python loadnsf.py $f
done

for f in dbdata/pickle/*-projects.pickle
do
   echo "Processing projects file $f"
   time python loadnsf.py $f
done
