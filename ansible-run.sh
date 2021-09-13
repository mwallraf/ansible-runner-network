#!/usr/bin/env bash

# logging-wrapper.sh
# Shell wrapper around Makefile for starting ansible-runner projects
#  Use this wrapper to create new ansible projects and run them
#  Users will need to have write permissions in the projects folder and also
#  have permissions to run docker commands

# Author: Maarten Wallraf
# Version: 1.0
# Date: 13-09-2021

# USAGE:
#
#  ansible-run -h                       : print help information
#
#  ansible-run -s                       : show location of projects folder
#  
#  ansible-run create <project>         : create a new project folder <project>
#                                         and changes the path to this new folder
#
#  ansible-run run <project> [playbook] : runs the playbook of a project inside
#                                         a new docker container which only exists
#                                         during the execution of the playbook
#                                         As an option the playbook name can be
#                                         provided

CURRPWD="$(pwd)"
SYMLINKDIR="$(dirname "$(readlink  "${BASH_SOURCE[0]}")")"
PROJECT_BASE="$SYMLINKDIR/projects"

DEFAULT_PLAYBOOK="playbook"
E_BADARGS=85   # Wrong number of arguments passed to script.



############################################################
# Help                                                     #
############################################################
Help()
{
   # Display Help
   echo "Create and run ansible projects."
   echo
   echo "Syntax: ansible-run [-hsc] <project> [playbook]"
   echo
   echo "Options:"
   echo "  -h          Print this Help."
   echo "  -c          Create a new ansible project."
   echo "  -s          Show the location of the projects folder."
   echo "  <project>  The name of the ansible project folder."
   echo "  <playbook> The name of the ansible playbook (default=playbook)."
   echo
}


Debug()
{
  echo "makedir: $SYMLINKDIR"
  echo "currpwd: $CURRPWD"
  echo "projectdir: $PROJECT_DIR"
  echo "project: $PROJECT"
  echo "playbook: $PLAYBOOK"
}

############################################################
# Checkgroup - make sure the user has docker perms         #
############################################################
Checkgroup()
{
  if ! $(docker ps | grep -q CONTAINER);
  then
    echo "you need docker privileges in order to run this command"
    exit
  fi
}


############################################################
# CreateProject - make a new ansible project               #
############################################################
CreateProject()
{
  if [[ -d "$PROJECT_BASE/$PROJECT" ]]
  then
    echo "the project folder '$PROJECT_BASE/$PROJECT' already exists"
    exit
  fi

  cd $SYMLINKDIR 2>&1 >/dev/null
  make project PROJECT=$PROJECT 2>&1 >/dev/null
}


CreateProjectConfirmation()
{
  read -p "Are you sure you want to create project '$PROJECT'? [y|N] " -n 1 -r
  echo    # (optional) move to a new line
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
    CreateProject

    echo
    echo "Project $PROJECT is created here: $PROJECT_BASE/$PROJECT"
    echo
    echo "Next steps:"
    echo "     - update the hosts file in the inventory folder"
    echo "     - create/update the ansible playbook in the project folder"
    echo "     - execute the project: ansible-run $PROJECT"
    echo
  fi
}


############################################################
# RunProject - run an existing ansible project             #
############################################################
RunProject()
{
  # exit if the project folder does not exists
  if [[ ! -d "$PROJECT_BASE/$PROJECT" ]]
  then
    echo "the project folder '$PROJECT_BASE/$PROJECT' does not exist - nothing to run"
    exit
  fi

  # exit if the playbook does not exist
  if [[ ! -f "$PROJECT_BASE/$PROJECT/project/$PLAYBOOK.yml" ]]
  then
    echo "the playbook '$PROJECT_BASE/$PROJECT/project/$PLAYBOOK.yml' does not exist - nothing to run"
    exit
  fi

  cd $SYMLINKDIR
  make run PROJECT=$PROJECT PLAYBOOK=$PLAYBOOK
}


RunProjectConfirmation()
{
  read -p "Are you sure you want to run project '$PROJECT'? [y|N] " -n 1 -r
  echo    # (optional) move to a new line
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
    RunProject

    echo
    echo "Script output can be found here: $PROJECT_DIR/artifacts"
  fi
}

############################################################
# ShowProjectFolder - show location of the projects folder #
############################################################
ShowProjectsFolder()
{
  echo "Project folder location: $PROJECT_BASE"
}

############################################################
############################################################
# Main program                                             #
############################################################
############################################################
############################################################
# Process the input options. Add options as needed.        #
############################################################
# Get the options
while getopts ":hsc:" option; do
   case $option in
      h) # display Help
         Help
         exit;;
      c) # CreateProject
         PROJECT=${OPTARG}
         CreateProjectConfirmation
         exit;;
      s) # Show projects folder
         ShowProjectsFolder
         exit;;
     \?) # Invalid option
         echo "Error: Invalid option"
         Help
         exit;;
   esac
done

# check user permissions
Checkgroup

# make sure we have minimal 1 parameter left
if [ $# -eq "0" ]
then
  Help
  exit
fi

# RUN the project
PROJECT="$1"
PROJECT_DIR="$PROJECT_BASE/$PROJECT"
if [ $# -gt "1" ]
then
  PLAYBOOK="$2"
else
  PLAYBOOK="$DEFAULT_PLAYBOOK"
fi

RunProjectConfirmation

# Debug

exit 0
