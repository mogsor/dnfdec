"""
the process:

0. figure out which groups and packages to install, etc.

1.  set every package as user-installed
    (this seems insane, but it means we can remove groups without removing any
    packages, which allows us to manage groups independently)

2.  remove all groups
    (gives us a clean break)

3.  install desired groups EXCLUDING unwanted packages
    (reinstalls existing, which brings in new dependencies, etc. and avoids
    installing unwanted packages just to delete them later)

4.  install explicitly desired packages
    (fills in any newly-added packages)

5.  set all packages to dependency, EXCLUDING explicitly desired packages
    (in dnf5, if a package is part of a group and you mark it as a dependency,
    it ends up marked as a group package and won't be removed on autoremove.
    while this is kind of annoying on paper it's quite useful in practice, as
    it means we can simply set every package as dependency and let dnf figure
    out which ones to keep grouped)
    (and then we exclude explicitly desired packages so they stay user marked)

6.  dnf autoremove
    (finally clears out anything undesireable)

an obvious problem with this approach is that it uses several dnf actions,
which will spam the history a bit. there's almost certainly a better approach
to this, but I'm not interested in learning the dnf5 api to find it, and
history rollback is still *usable* after all
"""


# SETUP


# imports
import configparser
import subprocess

# command shorthand
dnf = ["sudo", "dnf", "-q", "-y"]

# read config file
config = configparser.ConfigParser(allow_no_value=True)
config.read("packages.ini")


# PROCESS


# step 1. mark all packages as user installed

print("Marking packages as user installed...")

try:
    out = subprocess.run(
        dnf + ["mark", "user", "*"],
        capture_output=True,
        check=True
    )
except subprocess.CalledProcessError:
    print(out.stderr.decode())
    quit()


# step 2. remove all groups (now safe to do without removing packages)

print("Removing groups...")

try:
    subprocess.run(
        dnf + ["group", "remove", "*"],
        capture_output=True,
        check=True
    )
except subprocess.CalledProcessError:
    print(out.stderr.decode())
    quit()


# step 3. install desired groups, minus unwanted packages

try:
    out = subprocess.run(
        dnf + ["group", "install"] + list(config["groups"])
        + ["--exclude=" + ",".join(list(config["packages.exclude"]))],
        # capture_output=True,
        stderr=subprocess.DEVNULL,
        check=True
    )
except subprocess.CalledProcessError:
    print(out.stderr.decode())
    quit()


# step 4. install explicitly desired packages

try:
    out = subprocess.run(
        dnf + ["install"] + list(config["packages.install"]),
        # + ["--exclude=" + ",".join(list(config["packages.exclude"]))],
        # capture_output=True,
        stderr=subprocess.DEVNULL,
        check=True
    )
except subprocess.CalledProcessError:
    print(out.stderr.decode())
    quit()

# step 5. explicitly remove excluded packages

print("Removing excluded packages...")

try:
    out = subprocess.run(
        dnf + ["remove"] + list(config["packages.exclude"])
        + ["--exclude=" + ",".join(list(config["packages.install"]))],
        stderr=subprocess.DEVNULL,
        check=True
    )
except subprocess.CalledProcessError:
    print(out.stderr.decode())
    quit()

# step 6. set all packages to dependency except explicitly desired ones

print("Marking packages as dependencies...")

try:
    out = subprocess.run(
        dnf + ["mark", "dependency", "*"]
        + ["--exclude=" + ",".join(list(config["packages.install"]))],
        capture_output=True,
        # stderr=subprocess.DEVNULL,
        check=True
    )
except subprocess.CalledProcessError:
    print(out.stderr.decode())
    quit()

# step 7. dnf autoremove

print("Running dnf autoremove...")

try:
    out = subprocess.run(
        dnf + ["autoremove"],
        # capture_output=True,
        stderr=subprocess.DEVNULL,
        check=True
    )
except subprocess.CalledProcessError:
    print(out.stderr.decode())
    quit()

print("Complete.")
