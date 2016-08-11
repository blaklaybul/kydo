# Kydo Skeleton

## setup (do this once)

Make sure you have anaconda installed. Once you've cloned the repo, enter the directory and run `conda env create` - this will create a sandboxed conda environment with all the correct python libraries installed (as indicated in `environment.yml`)

## update (do this every time you pull)

Run `conda env update` to update the environment to reflect the latest changes to `environment.yml`

## Running the app

Activate the conda environment with `source activate kydo` and execute `python app/run_kydo.py`

Go to `localhost:3000` and authenticate your twitter account. You will be redirected to the console and it will begin print tweets corresponding to tracked users, keywords, and hashtags. 

## quiting the app

`^C` will exit the application, and `source deactivate` with deactivate your conda environment.
