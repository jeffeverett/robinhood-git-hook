# Robinhood Git Hook
This project allows users to fetch information about their current Robinhood positions.
Equities, options, and cryptocurrencies are supported.
Additionally, summary data about the user account is displayed.

The motivation behind the project was to attach the script to the Git hooking system such that
it runs after each commit. This can be used by the (perhaps not-so-small) demographic of Robinhood
users who also happen to be programmers to incentivize themselves into making more frequent commits.
Or, just to have a little fun.

Of course, the script is fully functional when not being used as a Git hook. Simply run the `check_portfolio.py`
script after the necessary installation steps.

# Installing the Package
First you must clone the repository: 
```
git clone https://github.com/jeffeverett/robinhood-git-hook.git
```

Then update the submodules:
```
git submodule update --init --recursive
```

Finally, install the requirements
```
pip install -r requirements.txt
```

At this point, the main script can be run as:
```
./check_portfolio.py
```

# Setting up with Git
Git hooks are essentially events that you can "hook" onto. You do so by creating script files in the `.git/hooks` directory;
the filename indicates the event which will cause the script to run. For more, see [here](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks).

To set a global Git hook directory that applies to all repositories, use the following command:
```
git config --global core.hooksPath ~/.git-hooks
```

Of course, `~/.git-hooks` can be replaced by any suitable path.

Now, create a symbolic link between the `post-commit` file in your chosen directory and the `check_portfolio.py`
script in the installation directory. For example:
```
ln -s ~/Downloads/robinhood-git-hook/check_portfolio.py ~/.git-hooks/post-commit
```
Here, `post-commit` is the Git hook that we're running our script for. You can use others as well, check the above link.

# Configuration
Configuration settings are stored in JSON format at `~/.robinhood-git-hook/config.json`. Currently, the following options
are supported:
- `save_token` - `true` or `false` (default). 
  - If `true`, store OAuth2 token in local filesystem to prevent having to log back in the next time the script runs.
  - If `false`, require log in on every script run.

Please be aware that storing the token is a security risk. It should not be stored for accounts of non-trivial value. If you do choose to store the token, take basic steps like encrypting your home folder and suitably managing the permissions.
