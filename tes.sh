if [ $1 = "up" ]
then
    echo "Both variables are the same"
elif [ $1 = "down" ]
then
    echo "Both variables are different"
else
    echo "The argument" $1 "is not recognized"
fi