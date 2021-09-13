# ANSIBLE-RUNNER-NETWORK

Docker worker image for ansible-runner.

The image has specific python and ansible galaxy requirements so that it can run playbooks on network equipment.

## ABOUT

This package allows users to run ansible projects in an isolated Docker container. A scaffolding structure is created for each new project and users should only update the ``ìnventory``` file and make the ansible ```playbook```. Then they will be able to run it without having to worry about additional environment variables or other parameters.

## INSTALLATION

To install this package download it from GIT, create the VAULT identity file and initialize it.
This step has to be done only once and should be done by an administrator or someone with sudo permissions and permissions to build Docker images.


**Download from GIT**

```
git clone https://github.com/mwallraf/ansible-runner-network.git
```

**Create the VAULT identity file**

If you want to use encrypted information in the environment variables then you'll have to create a vault identity file. You can create a file specifically for your project and in that case this step can be skipped, if you want to have a global identity file for all the projects then you'll have to add it in ```ansible_plugins/vault/.vault``` before building the docker image.

```
echo "your secret here" > ansible_plugins/vault/.vault
```

**Initialize the package**

In case a proxy connection is required then don't forget to set the ```http_proxy``` and ```https_proxy``` environment variables first

```
make init
```


## USAGE

Follow these instructions to create a new ansible project and to run it.

    > To use this package you will need to have permissions to run Docker commands, either via ```sudo``` or being a member of the linux ```docker``` group.

In order to create a new project and run it you will have to execute the commands below:

```
ansible-run -c show_running_config
ansible-run show_running_config
```    

To run a project called ```show_running_config``` with playbook called ```oneaccess``` run the command below. This assumes that there is a file called ```oneaccess.yml``` inside the ```show_running_config\project``` folder

```
ansible-run show_running_config oneaccess
```


### ansible-run

This is a wrapper script around Makefile that should be used to create and run ansible projects.

The ```ansible-run``` command is created while initializing the package and has the following parameters:

    **create <project>** : Create a new project folder called <project>

    **run <project> [<playbook>] : Run the playboook of a project



## CREATE A NEW PROJECT

Creating a new project means that a new ansible project folder will be created based on the ```demo``` project files. Usually you will only have to update the ```inventory``` and the ```project playbook``` and nothing else.

To create the new project use the ```ansible-run``` command. This will create your project folders and files and take you to the project folder.

```
ansible-run create <your project name>
```

### PROJECT FOLDERS

The structure of your project folder will look like below, the only files you will normally have to update are the ```inventory > hosts``` and ```project > playbook.yml``` files.

```
    -- env
        |-- cmdline
        |-- envvars
        |-- extravars
        |-- passwords
        |-- settings
        |-- ssh_key
    -- inventory
        |-- hosts
    -- project
        |-- roles
        |-- playbook.yml
```

### INVENTORY

The inventory hosts file contains all the hosts or ip addresses that you will run your script on. Normally you only need a single hosts file but if you create multiple files then you probably will have to update the ```env/cmdline``` file to match the correct hosts filename.

Check the [Ansible reference](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html) for the exact syntax.


### ANSIBLE PLAYBOOK

The actual ansible playbook and ansible roles are located in the ```project``` folder. The ```playbook.yml``` file and ```roles``` folder are just an example and you will have to update or replace them according to your needs.

The default playbook name being used is ```playbook.yml``` but you can create as many playbook files as you want and provide them as a parameter to the ```ansible-run``` script.

For more information about playbooks check out the [Ansible](https://docs.ansible.com) website




