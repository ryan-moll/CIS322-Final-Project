# Project 7: Adding authentication and user interface to brevet time calculator service

## Info

* Author: Ryan Moll


## Overview:

* This project is a calculator built to calculate open times and close times for checkpoints in a brevet. It does so using Flask to handle the page serving and mongoDB to store the data. It also offers APIs which can be accessed to get the open and close times in JSON or CSV format. These APIs are protected, and require a token. This token can be provided two ways:

	1. The user can register and login on the frontend of the server. Upon logging in, a token will be generated and that token will remain valid for 10 minutes. During those 10 minutes, the user has free reign to access all of the APIs. Should they want to see their current token, they can navigate to the page at "http://0.0.0.0:5000/api/token" which will reveal their current active token and its duration in a JSON dict. Should they want to refresh their token, they must login again to prove that they are still a valid user.

	2. The other way a user can generate a token is by making a GET request via curl (or a comparable service) to "http://0.0.0.0:5000/api/token". In that request, the user must provide valid login credentials in a dictionary of the form {"username":"password"} for the "authorization" value (on curl this is denoted with the "-u" flag). This will return a JSON dict with a newly generated token corresponding to that user, and the duration that that token is valid in seconds. This token can be used to generate more tokens so that the user can effectively stay logged in.

		* A curl request to generate a token for a user with the username "Steven" and the password "Kitten123" would look like this:
			```
			curl -i -X POST -H "Content-Type: application/json" -d '{"username":"Steven","password":"Kitten123"}' http://127.0.0.1:5000/api/register
			```

* If you don't have a username and password yet, you can register a new user. Once again, this can be done two ways:

	1. First, you can user the frontend to register a new user. Navigate to the homepage at "http://0.0.0.0:5000/" and click "register" in the top-right corner. Here you can create a new user with a username and valid password. If the username is already taken, or the password is not at leat 8 characters in length, the user will not be created. You will know if your user was successfully created if you are redirected to the login page after clicking register. Here you can log in the user you just created. And don't worry about your password being stolen! It is hashed before it is stored in the database.

	2. Alternatively, you can once again make a POST request via curl or a comparable service to "http://0.0.0.0:5000/api/register". In the request, you must provide a data value (-d) that is a dictionary with the following format: "{"username":"<yourusername>", "password":"<yourpassword>"}". Assuming the username and password are valid, the user will be created and added to the database, and a JSON object will be returned containing the newly created user, and a Location header containing the URI at which you can access that user. Once again, if the username is already taken, or the password is not at leat 8 characters in length, the user will not be created.

				* A curl request to create a new user with the username "Steven" and the password "Kitten123" would look like this:
			```
			curl -u Steven:Kitten123 -i -X GET http://127.0.0.1:5000/api/token
			```

* To run the project, execute the commands "docker-compose build" and "docker-compose up" to build the docker containers and run them. Next, you should navigate to the page at "http://0.0.0.0:5000/" in a browser. This is the html landing page where you can plan out your brevet and submit your data. The page will do its best to prevent you from submitting invalid data or displaying if the database is empty. This is revealed if you hover your mouse over the disabled buttons. Once you have entered valid data and submitted, you can view your data with the 'display' button. If you are not logged in, a login and register button will be available at the top right corner of the index page. If you have logged in, a logout button will be available, allowing you to log out. 

	* On the login page, a remember me button is available. Should you check this button, your user will remain logged in even if you close your browser. 

	* Requests made through this webservice are protected from CSRF attacks

* Available APIs: (All token protected)

	* http://0.0.0.0:5001/listAll or http://0.0.0.0:5001/listAll/json will provide both the open and close times for each checkpoint in JSON format

	* http://0.0.0.0:5001/listOpenOnly or http://0.0.0.0:5001/listOpenOnly/json will provide only the open time for each checkpoint in JSON format

	* http://0.0.0.0:5001/listCloseOnly or http://0.0.0.0:5001/listCloseOnly/json will provide only the close time for each checkpoint in JSON format

	* http://0.0.0.0:5001/listAll/csv will provide both the open and close times for each checkpoint in CSV format

	* http://0.0.0.0:5001/listOpenOnly/csv will provide only the open time for each checkpoint in CSV format

	* http://0.0.0.0:5001/listCloseOnly/csv will provide only the close time for each checkpoint in CSV format

		* Note: The CSV endpoints will automatially download the CSV formatted data as a .csv file onto your computer. From there you can open the data in excel or use it however you like.

		* Each endpoint can be limited with the 'top' parameter. Simply add "?top=<int>" to make the api return only the top 'k' values of the query where 'k' is the integer you passed in as the top parameter.