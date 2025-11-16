# GACPD
A tool developed using Pareco's backend to improve upon its detection capabilities for divergent branches. GACPD combines both [Pareco](https://github.com/unlv-evol/PaReco/) and [JSCPD](https://github.com/kucherenko/jscpd) to obtain the divergent's branches pull requests (PRs) which GACPD then processed in such a manner in which the obtained .patch files are then converted into the correct programming language. From then the .patch files hungs are processed to obtained the changed lines and saved in individual files. JSCPD is used specifically with to Pareco for its tokenizer and normalizer for over 140 different programming languages.

Those individual files are then compared to the main branch's current version to find if there has an effort duplication (ED), a missed opportunity (MO), both (split case [SP]) or if the file has been completely deleted.

Current Directory Structure
```
├── LICENSE
├── README.md
├── tokens-example.txt
├── GACPD.ipynb
├── requirements.txt
├── package.json
├── package-lock.json
├── .jscpd.json
├── node_modules
├── Methods
├── GACPD
└── 
```

# Setting up
To set up `GACPD` you will need to do the following steps:
```
git clone https://github.com/unlv-evol/GACPD
```

# Minimum Requirements
``OS``: Windows, linux, MacOS
``RAM``: 4GB
``Storage``: 1GB
``Python``: 3.12
``PIP``: 24

# Download NPM
Follow the official documentation of NPM 
```
https://docs.npmjs.com/downloading-and-installing-node-js-and-npm
```

# Installing the packages
After having NPM installed run the following command to install JSCPD
```
npm install
```
This command will directly install of the provided package.json and package-lock.json files

# Install requirements
```
pip install -r requirements.txt
```

# Github Tokens
We use [GitHub tokens](https://github.com/settings/tokens) when extracting PR patches. This allows for higher rate limit because of the high number of requests to the GitHub API. Tokens can be set in the tokens.txt file seperated by a comman. The user can add as many tokens as needed. A minimal of 2 tokens can be used to safely execute code and to make sure that the rate limit is not reached for a token.