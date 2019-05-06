# udacity-fsd-proj-item-catalog

## Udacity Full Stack Developer Project - Item Catalog
A simple python flask application, serving a web page that enables NHL team roster management. Signing in with Google allows creating new players, and editing/deleting players you created. You will not be authorized to edit/delete players created by other users, but you will be able to browse through their details.

### VM Setup

You'll need to install [VirtualBox6.0](https://www.virtualbox.org/wiki/Downloads) and [Vagrant](https://www.vagrantup.com/downloads.html).

Next, you need to clone this project and spin up the Vagrant VM. You can use whatever terminal you prefer (GitBash works well on Windows).
````
user@host:~$ git clone https://github.com/mach21/udacity-fsd-proj-item-catalog.git
user@host:~$ cd udacity-fsd-proj-item-catalog/vagrant
user@host:~$ vagrant up
user@host:~$ vagrant ssh
vagrant@vagrant:~$ cd /vagrant/catalog
````

### Bootstrapping

First, we need to make sure Google recognizes this app and provides sign-in functionality. Edit the **client_secrets.json** file in your text editor of choice, and replace **YOUR_CLIENT_ID** and **YOUR_CLIENT_SECRET**.

Next, this command will install the basic environment prerequisites:

````
vagrant@vagrant:/vagrant/catalog$ chmod +x bootstrap.sh && ./bootstrap.sh
````

### Virtual Environment

Install package dependencies and activate the python virtual environment with:

````
vagrant@vagrant:/vagrant/catalog$ source dev-virtenv.sh
````

### Pre-populate DB

````
vagrant@vagrant:/vagrant/catalog$ python3 db_populate.py
````

### Run the Server

We're finally ready to run the flask server:

````
vagrant@vagrant:/vagrant/catalog$ python3 -m server
````

### Play Around
Point the browser on your host machine to http://localhost:8000/ and play around. Hint: the Nashville Predators are an interesting team, check them out!
You will only be allowed to create new players after logging in with Google (hit the Login button in the upper right corner). You will only be allowed to edit/delete players you created. You will be allowed to view all teams and players, regardless of login status.

### Stop the Server

Press Ctrl-C in the terminal.

### Stop the VM

````
vagrant@vagrant:/vagrant/catalog$ exit
user@host:~$ vagrant halt
````
