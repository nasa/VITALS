# Contributing to this Repository

We want your help! Even if you're not a coder! There are several ways you can contribute to this repository:

- Report an [Issue]() or make a recommendation
- Update code, documentation, notebooks or other files (even fixing typos)
- Propose a new notebook

In the sections below we outline how to approach each of these types of contributions. If you're new to GithHub, you can [sign up here](https://github.com/). There are a bunch of great resources for those new to Git and GitHub in the [Starting out with Git and Github](#starting-out-with-git-and-github) section. If you have any questions or concerns, please reach out: [lpdaac@usgs.gov](lpdaac@usgs.gov).  

## Report an Issue or Make a Recommendation

If you've found a problem with the repository, we want to know about it. Please submit an [Issue](). Before submitting, please check to see if a similar issue already exists. If not, create a new issue, providing as much detail as possible. Things like screenshots and code excerpts demonstrating the problem are very helpful!

## Updating Code, Documentation, Notebooks, or Other Files

To contribute a solution to an issue or make a change to files within the repository we've created a typical outline of how to do that below. If you're just starting out with git and Github, please see the [Starting out with git and Github](#starting-out-with-git-and-github) section. If you want to make a simple change, like correcting a typo within a markdown document or other documentation, there's a great video explaining how to do that [here](https://www.youtube.com/watch?v=PHoScPeMWHI)
To make a more complex change to a notebook, code, or other file follow the instructions below.

1. Please create an issue or comment on an existing issue describing the changes you intend to make.  
2. Create a [fork](https://docs.github.com/en/get-started/quickstart/contributing-to-projects#about-forking) of this repository to create your own copy of the repository. When working from your fork, you can do whatever you want, you won't mess up anyone else's work so you're safe to try things out. Worst case scenario you can delete your fork and recreate it.  
3. Clone your fork to your local computer:  

    ```
    git clone your-fork-repository-url
    ```

    - Change directories

    ```
    cd repository-name
    ```

    - Add the upstream repository

    ```
    git remote add upstream original-repository-url
    ```

    - Using `git remote -v` will show two remote repositories named:  
        - `upstream`, which refers to the repository  
        - `origin`, which refers to your personal fork  
    - Often, updates to an `upstream` repository will occur while you are developing changes on your personal fork. You can pull the latest changes from `upstream`, including tags:

    ```
    git checkout dev
    git pull upstream dev --tags
    ```

4. Develop your contribution:
    - Create a new branch named appropriately for the feature you want to work on:

    ```
    git checkout -b feature-name
    ```

    - Commit locally as you progress using `git add` and `git commit`. You can check the status of your local copy of the repository using

    ```
    ```

5. To submit your contribution, push your changes back to your fork on Github:

    ```git
    git push origin feature-name
    ```

    - Enter username and password, depending on your settings, you may need to use a [Personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
    - Make a Pull Request. On the GitHub page for your personal fork, there will be a green Pull Request button.    -

## Adding New Notebooks or Example Workflows

In the spirit of open science, we want to minimize barriers to sharing code and examples. We have added a `user_contributed` directory to the repository for anyone to share examples of their work in notebook or code form. Documentation and descriptions do not need to be as thorough as the examples we've created, but we ask that you provide as much as possible. Follow the contributor instructions above, placing your new notebook or module in a suitably named directory within the `user_contributed` directory. Be sure to remove any large datasets, indicating where users can retrieve them.

## Starting out with git and Github

If you're just starting out with git and GitHub, the [Github Quickstart page](https://docs.github.com/en/get-started/quickstart) has some helpful documents.

**Other Helpful Links:**

- [GitHub Cheatsheet](https://training.github.com/downloads/github-git-cheat-sheet/)

## Attribution

These contributing guidelines are adapted from the NASA Transform to Open Science github, available at <https://github.com/nasa/Transform-to-Open-Science/blob/main/CONTRIBUTING.md>.
