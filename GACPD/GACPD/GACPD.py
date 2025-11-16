import os
import pprint
import sys, platform
import json
import pandas as pd
import shutil
import subprocess
import matplotlib.pyplot as plt
import time
# import Methods.totals as totals
import NewPaReco.utils.totals as totals
from collections import defaultdict
# import Methods.analysis as analysis
import NewPaReco.utils.analysis as analysis
# import Methods.classifier as classifier
import NewPaReco.core.classifier as classifier
# import Methods.dataLoader as dataloader
import NewPaReco.core.data_extractor as dataloader
# import Methods.common as common
import NewPaReco.utils.common as common
# import Methods.commitLoader as commitloader
import NewPaReco.utils.helpers as commitloader
from NewPaReco.constants import constant
from NewPaReco.utils import helpers
# from Methods.patchExtractionFunctions import divergence_date
from NewPaReco.utils.helpers import divergence_date
# from Methods.patchExtractionFunctions import pr_patches
from NewPaReco.core.patch_extractor import pullrequest_patches
from NewPaReco.core.patch_extractor_branches import pullrequest_patches_branch
import requests


class GACPD:
    def __init__(self, params, branch=False):
        if branch is False:
            self.repo_check_number, self.repo_main_line, self.repo_divergent, self.token_list, self.divergence_date, self.cut_off_date = params
            self.token_count = len(self.token_list)
            self.repo_data = []
            self.results = {}
            self.main_dir_results = 'Results/Repos_results/'
            self.repo_dir_files = 'Results/Repos_files/'
            self.repo_clones = 'Results/Repos_clones/'
            self.pr_classifications = {}
            self.prs = []
            self.file_extensions_swapped = {
                ".abap": "abap",
                ".as": "actionscript",
                ".adb": "ada",
                ".ads": "ada",
                ".apl": "apl",
                ".applescript": "applescript",
                ".ino": "arduino",
                ".pde": "processing",
                ".arff": "arff",
                ".adoc": "asciidoc",
                ".asciidoc": "asciidoc",
                ".asm": "nasm",
                ".s": "asm6502",
                ".aspx": "aspnet",
                ".ascx": "aspnet",
                ".ahk": "autohotkey",
                ".au3": "autoit",
                ".sh": "bash",
                ".bash": "bash",
                ".bas": "basic",
                ".cmd": "batch",
                ".y": "bison",
                ".b": "brainfuck",
                ".bf": "brainfuck",
                ".bro": "bro",
                ".c": "c",
                ".h": "c-header",
                ".clj": "clojure",
                ".cljs": "clojure",
                ".cljc": "clojure",
                ".coffee": "coffeescript",
                ".cpp": "cpp",
                ".cc": "cpp",
                ".cxx": "cpp",
                ".hpp": "cpp-header",
                ".hxx": "cpp-header",
                ".hh": "cpp-header",
                ".cr": "crystal",
                ".cs": "csharp",
                ".csp": "csp",
                ".css": "css",
                ".d": "d",
                ".dart": "dart",
                ".diff": "diff",
                ".patch": "diff",
                "Dockerfile": "docker",
                ".dockerfile": "docker",
                ".e": "eiffel",
                ".ev": "eiffel",
                ".ex": "elixir",
                ".exs": "elixir",
                ".elm": "elm",
                ".erb": "erb",
                ".erl": "erlang",
                ".hrl": "erlang",
                ".f": "fortran",
                ".for": "fortran",
                ".f90": "fortran",
                ".f95": "fortran",
                ".fs": "fsharp",
                ".fsi": "fsharp",
                ".fsx": "fsharp",
                ".ged": "gedcom",
                ".feature": "gherkin",
                ".glsl": "glsl",
                ".vert": "glsl",
                ".frag": "glsl",
                ".go": "go",
                ".graphql": "graphql",
                ".gql": "graphql",
                ".groovy": "groovy",
                ".gvy": "groovy",
                ".haml": "haml",
                ".hbs": "handlebars",
                ".handlebars": "handlebars",
                ".hs": "haskell",
                ".hx": "haxe",
                ".http": "http",
                ".icn": "icon",
                ".ini": "ini",
                ".cfg": "ini",
                ".io": "io",
                ".ijs": "j",
                ".java": "java",
                ".js": "javascript",
                ".mjs": "javascript",
                ".ol": "jolie",
                ".iol": "jolie",
                ".json": "json",
                ".jsx": "jsx",
                ".jl": "julia",
                ".keymap": "keymap",
                ".kt": "kotlin",
                ".kts": "kotlin",
                ".tex": "latex",
                ".sty": "latex",
                ".cls": "latex",
                ".less": "less",
                ".liquid": "liquid",
                ".lisp": "lisp",
                ".lsp": "lisp",
                ".cl": "lisp",
                ".ls": "livescript",
                ".lol": "lolcode",
                ".lua": "lua",
                "Makefile": "makefile",
                ".mk": "makefile",
                ".md": "markdown",
                ".markdown": "markdown",
                ".html": "markup",
                ".xml": "markup",
                ".xhtml": "markup",
                ".m": "objectivec",
                ".mel": "mel",
                ".miz": "mizar",
                ".monkey": "monkey",
                ".n4js": "n4js",
                ".nasm": "nasm",
                ".nim": "nim",
                ".nims": "nim",
                ".nix": "nix",
                ".nsi": "nsis",
                ".nsh": "nsis",
                ".mm": "objectivec",
                ".ml": "ocaml",
                ".mli": "ocaml",
                ".cl": "opencl",
                ".oz": "oz",
                ".gp": "parigp",
                ".pas": "pascal",
                ".pl": "perl",
                ".pm": "perl",
                ".php": "php",
                ".phtml": "php",
                ".pls": "plsql",
                ".plsql": "plsql",
                ".ps1": "powershell",
                ".psm1": "powershell",
                ".pde": "processing",
                ".pro": "prolog",
                ".properties": "properties",
                ".proto": "protobuf",
                ".pug": "pug",
                ".jade": "pug",
                ".pp": "puppet",
                ".pure": "pure",
                ".py": "python",
                ".pyw": "python",
                ".q": "q",
                ".r": "r",
                ".R": "r",
                ".re": "reason",
                ".rpy": "renpy",
                ".rest": "rest",
                ".rst": "rest",
                ".rip": "rip",
                ".graph": "roboconf",
                ".instances": "roboconf",
                ".rb": "ruby",
                ".rs": "rust",
                ".sas": "sas",
                ".sass": "sass",
                ".scala": "scala",
                ".scm": "scheme",
                ".ss": "scheme",
                ".scss": "scss",
                ".st": "smalltalk",
                ".tpl": "smarty",
                ".soy": "soy",
                ".sql": "sql",
                ".styl": "stylus",
                ".swift": "swift",
                ".tap": "tap",
                ".tcl": "tcl",
                ".textile": "textile",
                ".tsx": "tsx",
                ".tt2": "tt2",
                ".twig": "twig",
                ".ts": "typescript",
                ".vb": "visual-basic",
                ".vm": "velocity",
                ".v": "verilog",
                ".vh": "verilog",
                ".vhdl": "vhdl",
                ".vhd": "vhdl",
                ".vim": "vim",
                ".wat": "wasm",
                ".wasm": "wasm",
                ".wiki": "wiki",
                ".mediawiki": "wiki",
                ".xeora": "xeora",
                ".xeoracube": "xeora",
                ".xojo_code": "xojo",
                ".xojo_window": "xojo",
                ".xq": "xquery",
                ".xquery": "xquery",
                ".yaml": "yaml",
                ".yml": "yaml"
            }
            self.pareco_extensions = ["c", "java", "python", "bash", "prolog", "php", "ruby"]
            self.renames = {}
            self.cycles = []
        else:
            self.repo_number, self.repo_main_line, self.repo_divergent, self.token_list = params
            self.token_count = len(self.token_list)
            self.repo_data = []
            self.results = {}
            self.main_dir_results = 'Results/Branch_results/'
            self.repo_dir_files = 'Results/Branch_files/'
            self.repo_clones = 'Results/Branch_clones/'
            self.pr_classifications = {}
            self.prs = []
            self.file_extensions_swapped = {
                ".abap": "abap",
                ".as": "actionscript",
                ".adb": "ada",
                ".ads": "ada",
                ".apl": "apl",
                ".applescript": "applescript",
                ".ino": "arduino",
                ".pde": "processing",
                ".arff": "arff",
                ".adoc": "asciidoc",
                ".asciidoc": "asciidoc",
                ".asm": "nasm",
                ".s": "asm6502",
                ".aspx": "aspnet",
                ".ascx": "aspnet",
                ".ahk": "autohotkey",
                ".au3": "autoit",
                ".sh": "bash",
                ".bash": "bash",
                ".bas": "basic",
                ".cmd": "batch",
                ".y": "bison",
                ".b": "brainfuck",
                ".bf": "brainfuck",
                ".bro": "bro",
                ".c": "c",
                ".h": "c-header",
                ".clj": "clojure",
                ".cljs": "clojure",
                ".cljc": "clojure",
                ".coffee": "coffeescript",
                ".cpp": "cpp",
                ".cc": "cpp",
                ".cxx": "cpp",
                ".hpp": "cpp-header",
                ".hxx": "cpp-header",
                ".hh": "cpp-header",
                ".cr": "crystal",
                ".cs": "csharp",
                ".csp": "csp",
                ".css": "css",
                ".d": "d",
                ".dart": "dart",
                ".diff": "diff",
                ".patch": "diff",
                "Dockerfile": "docker",
                ".dockerfile": "docker",
                ".e": "eiffel",
                ".ev": "eiffel",
                ".ex": "elixir",
                ".exs": "elixir",
                ".elm": "elm",
                ".erb": "erb",
                ".erl": "erlang",
                ".hrl": "erlang",
                ".f": "fortran",
                ".for": "fortran",
                ".f90": "fortran",
                ".f95": "fortran",
                ".fs": "fsharp",
                ".fsi": "fsharp",
                ".fsx": "fsharp",
                ".ged": "gedcom",
                ".feature": "gherkin",
                ".glsl": "glsl",
                ".vert": "glsl",
                ".frag": "glsl",
                ".go": "go",
                ".graphql": "graphql",
                ".gql": "graphql",
                ".groovy": "groovy",
                ".gvy": "groovy",
                ".haml": "haml",
                ".hbs": "handlebars",
                ".handlebars": "handlebars",
                ".hs": "haskell",
                ".hx": "haxe",
                ".http": "http",
                ".icn": "icon",
                ".ini": "ini",
                ".cfg": "ini",
                ".io": "io",
                ".ijs": "j",
                ".java": "java",
                ".js": "javascript",
                ".mjs": "javascript",
                ".ol": "jolie",
                ".iol": "jolie",
                ".json": "json",
                ".jsx": "jsx",
                ".jl": "julia",
                ".keymap": "keymap",
                ".kt": "kotlin",
                ".kts": "kotlin",
                ".tex": "latex",
                ".sty": "latex",
                ".cls": "latex",
                ".less": "less",
                ".liquid": "liquid",
                ".lisp": "lisp",
                ".lsp": "lisp",
                ".cl": "lisp",
                ".ls": "livescript",
                ".lol": "lolcode",
                ".lua": "lua",
                "Makefile": "makefile",
                ".mk": "makefile",
                ".md": "markdown",
                ".markdown": "markdown",
                ".html": "markup",
                ".xml": "markup",
                ".xhtml": "markup",
                ".m": "objectivec",
                ".mel": "mel",
                ".miz": "mizar",
                ".monkey": "monkey",
                ".n4js": "n4js",
                ".nasm": "nasm",
                ".nim": "nim",
                ".nims": "nim",
                ".nix": "nix",
                ".nsi": "nsis",
                ".nsh": "nsis",
                ".mm": "objectivec",
                ".ml": "ocaml",
                ".mli": "ocaml",
                ".cl": "opencl",
                ".oz": "oz",
                ".gp": "parigp",
                ".pas": "pascal",
                ".pl": "perl",
                ".pm": "perl",
                ".php": "php",
                ".phtml": "php",
                ".pls": "plsql",
                ".plsql": "plsql",
                ".ps1": "powershell",
                ".psm1": "powershell",
                ".pde": "processing",
                ".pro": "prolog",
                ".properties": "properties",
                ".proto": "protobuf",
                ".pug": "pug",
                ".jade": "pug",
                ".pp": "puppet",
                ".pure": "pure",
                ".py": "python",
                ".pyw": "python",
                ".q": "q",
                ".r": "r",
                ".R": "r",
                ".re": "reason",
                ".rpy": "renpy",
                ".rest": "rest",
                ".rst": "rest",
                ".rip": "rip",
                ".graph": "roboconf",
                ".instances": "roboconf",
                ".rb": "ruby",
                ".rs": "rust",
                ".sas": "sas",
                ".sass": "sass",
                ".scala": "scala",
                ".scm": "scheme",
                ".ss": "scheme",
                ".scss": "scss",
                ".st": "smalltalk",
                ".tpl": "smarty",
                ".soy": "soy",
                ".sql": "sql",
                ".styl": "stylus",
                ".swift": "swift",
                ".tap": "tap",
                ".tcl": "tcl",
                ".textile": "textile",
                ".tsx": "tsx",
                ".tt2": "tt2",
                ".twig": "twig",
                ".ts": "typescript",
                ".vb": "visual-basic",
                ".vm": "velocity",
                ".v": "verilog",
                ".vh": "verilog",
                ".vhdl": "vhdl",
                ".vhd": "vhdl",
                ".vim": "vim",
                ".wat": "wasm",
                ".wasm": "wasm",
                ".wiki": "wiki",
                ".mediawiki": "wiki",
                ".xeora": "xeora",
                ".xeoracube": "xeora",
                ".xojo_code": "xojo",
                ".xojo_window": "xojo",
                ".xq": "xquery",
                ".xquery": "xquery",
                ".yaml": "yaml",
                ".yml": "yaml"
            }
            self.pareco_extensions = ["c", "java", "python", "bash", "prolog", "php", "ruby"]
            self.renames = {}
            self.cycles = []
        self.ct = 0

    def extract_branch_patches(self):
        print(f'Extracting patches for {self.repo_main_line} and {self.repo_divergent}...')
        repo = self.repo_main_line.split("/")
        pr_patch_ml, pr_title_ml, self.ct = pullrequest_patches_branch(repo[0]+"/"+repo[1], repo[2], self.token_list, self.ct)

        # at least one of the mainline or fork should have a pr with patch
        if len(pr_patch_ml) > 0:
            if len(pr_patch_ml) > 1:
                pr_patch_ml_str = '/'.join(map(str, pr_patch_ml))
                pr_title_ml_str = '=/='.join(map(str, pr_title_ml))
            if len(pr_patch_ml) == 1:
                pr_patch_ml_str = pr_patch_ml[0]
                pr_title_ml_str = pr_title_ml[0]

        df_data = []
        for i in range(len(pr_patch_ml)):
            df_data.append([pr_patch_ml[i], pr_title_ml[i]])

        self.df_patches = pd.DataFrame(df_data, columns=['Patch number', 'Patch title'])

        return pr_patch_ml

    def set_prs(self, prs):
        for pr in prs:
            self.prs.append(str(pr))

    def get_single_dates(self):
        self.fork_date, self.divergence_date, self.cut_off_date, self.ahead_by, self.behind_by, self.ct = divergence_date(
            self.repo_main_line, self.repo_divergent, self.token_list, self.token_count, self.cut_off_date, self.divergence_date)
        self.modern_day = self.cut_off_date

    def get_dates(self):
        self.fork_date, self.divergence_date, self.cut_off_date, self.ahead_by, self.behind_by, self.ct = divergence_date(
            self.repo_main_line, self.repo_divergent, self.token_list, self.token_count, self.cut_off_date, self.divergence_date)
        self.modern_day = self.cut_off_date
        print(
            f'The divergence_date of the repository {self.repo_divergent} is {self.divergence_date} and the cut_off_date is {self.cut_off_date}.')
        print(f'The variant2 is ==>')
        print(f'\t Ahead by {self.ahead_by} commits')
        print(f'\t Behind by {self.behind_by} commits')
        print(
            f'Select an interval within the period [{self.divergence_date}, {self.cut_off_date}] to limit the patches being checked.')

    def jscpd_bin(self):
        # Prefer npx if available (handles Windows/Unix, no path quirks)
        npx = shutil.which("npx")
        if npx:
            return [npx, "jscpd"]
        # Fallback to local .bin shims (Windows uses .cmd)
        bin_dir = os.path.join(os.getcwd(),"GACPD", "node_modules", ".bin")
        if platform.system() == "Windows":
            return [os.path.join(bin_dir, "jscpd.cmd")]
        return [os.path.join(bin_dir, "jscpd")]

    def createDf(self):
        df_data_files = []
        df_data_patches = []

        for pr in self.results:
            for file in self.results[pr]:
                try:
                    if self.results[pr][file]['result']['patchClass'] in ['ED', 'MO', 'SP']:
                        df_data_files.append(
                            [self.repo_main_line, self.repo_divergent, pr, file, self.results[pr][file]['result']['type'],
                             self.results[pr][file]['result']['patchClass'], 1])
                    else:
                        df_data_files.append([self.repo_main_line, self.repo_divergent, pr, file, 'None',
                                              self.results[pr][file]['result']['patchClass'], 0])
                    #print(self.results[pr][file])
                except Exception as e:
                    pass

            if self.pr_classifications[pr]["class"] in ['ED', 'MO', 'SP']:
                df_data_patches.append([self.repo_main_line, self.repo_divergent, pr, self.pr_classifications[pr]["class"], 1])
            else:
                df_data_patches.append([self.repo_main_line, self.repo_divergent, pr, self.pr_classifications[pr]["class"], 0])

        self.df_files_classes = pd.DataFrame(df_data_files,
                                             columns=['Mainline', 'Fork', 'Pr nr', 'Filename', 'Operation',
                                                      'File classification', 'Interesting'])
        self.df_files_classes = self.df_files_classes.sort_values(by=['Pr nr', 'Interesting'], ascending=False)

        self.df_patch_classes = pd.DataFrame(df_data_patches,
                                             columns=['Mainline', 'Fork', 'Pr nr', 'Patch classification',
                                                      'Interesting'])
        self.df_patch_classes = self.df_patch_classes.sort_values(by='Interesting', ascending=False)

    def printResults(self):
        print('\nClassification results:')
        for pr in self.results:
            print('\n')
            print(f'{self.repo_main_line} -> {self.repo_divergent}')
            print(f'Pull request nr ==> {pr}')
            #             print('\n')
            print('File classifications ==> ')
            for file in self.results[pr]:
                if self.results[pr][file]["result"]["patchClass"] in ['ED', 'MO', 'SP']:
                    print(f'\t {file}')
                    print(f'\t\t Operation - {self.results[pr][file]["result"]["type"]}')
                    print(f'\t\t Class - {self.results[pr][file]["result"]["patchClass"]}')
                else:
                    print(f'\t {file}')
                    print(f'\t\t Class - {self.results[pr][file]["result"]["patchClass"]}')
            print(f'Patch classification ==> {self.pr_classifications[pr]["class"]}')

    def parse_patch_file(self, patch_file, output_dir, extension):
        with open(patch_file, 'r') as patch:
            hunk_count = 0
            add_count = 0
            del_count = 0
            line_count = 0
            additions_file = []
            deletions_file = []
            context_file = []

            for line in patch:
                # Detect the start of a new hunk (lines starting with "@@")
                if line.startswith('@@'):
                    if hunk_count >= 0:
                        self.save_hunk_files(hunk_count, output_dir, deletions_file, del_count, f"deletions.{extension}")
                        self.save_hunk_files(hunk_count, output_dir, additions_file, add_count, f"additions.{extension}")
                        self.save_hunk_files(hunk_count, output_dir, context_file, line_count, f"context.{extension}")
                    hunk_count += 1
                    additions_file = []
                    deletions_file = []
                    context_file = []

                if line.startswith('+') and not line.startswith("+++"):
                    additions_file.append(line[1:])
                    add_count += 1
                elif line.startswith('-') and not line.startswith("---"):
                    deletions_file.append(line[1:])
                    del_count += 1
                elif not line.startswith("---") and not line.startswith("+++") and not line.startswith('@@'):
                    additions_file.append(line)
                    deletions_file.append(line)
                    context_file.append(line)
                    line_count += 1

            # Process the last hunk if any
            if deletions_file or additions_file:
                self.save_hunk_files(hunk_count, output_dir, deletions_file, del_count, f"deletions.{extension}")
                self.save_hunk_files(hunk_count, output_dir, additions_file, add_count, f"additions.{extension}")
                self.save_hunk_files(hunk_count, output_dir, context_file, line_count, f"context.{extension}")

    def save_hunk_files(self, hunk_id, output_dir, additions_hunks, counts, type_of_change):
        os.makedirs(output_dir, exist_ok=True)

        # Write the hunk with only additions to the additions file, if applicable
        if counts != 0:
            additions_file_path = os.path.join(output_dir, f'hunk_{hunk_id}_{type_of_change}')
            with open(additions_file_path, 'w') as add_file:
                add_file.writelines(additions_hunks)
            # print(f"Saved additions file for hunk {hunk_id}: {additions_file_path}")

    def extractPatches(self, chosen_diverge_date, chosen_cut_off_date):
        self.diverge_date = chosen_diverge_date
        self.cut_off_date = chosen_cut_off_date
        print(f'Extracting patches between {self.diverge_date} and {self.cut_off_date}...')

        pr_patch_ml_str = ''
        pr_title_ml_str = ''

        pr_patch_ml, pr_title_ml, self.ct = pullrequest_patches(self.repo_main_line, self.diverge_date,
                                                                         self.cut_off_date, self.token_list, self.ct)

        # at least one of the mainline or fork should have a pr with patch
        if len(pr_patch_ml) > 0:
            if len(pr_patch_ml) > 1:
                pr_patch_ml_str = '/'.join(map(str, pr_patch_ml))
                pr_title_ml_str = '=/='.join(map(str, pr_title_ml))
            if len(pr_patch_ml) == 1:
                pr_patch_ml_str = pr_patch_ml[0]
                pr_title_ml_str = pr_title_ml[0]

        df_data = []
        for i in range(len(pr_patch_ml)):
            df_data.append([pr_patch_ml[i], pr_title_ml[i]])

        self.df_patches = pd.DataFrame(df_data, columns=['Patch number', 'Patch title'])


        return pr_patch_ml

    def remove_all_files(self, directory_path):
        # Check if the directory exists
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            # Loop through all files and directories in the specified directory
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                try:
                    # Remove file if it's a file, or recursively delete if it's a directory
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            print("The specified directory does not exist or is not a directory.")

    def visualizeResults(self):
        print(f'\nBar plot of the patch classifications for {self.repo_main_line} -> {self.repo_divergent}')
        total_NA = 0
        total_ED = 0
        total_MO = 0
        total_CC = 0
        total_SP = 0
        total_NE = 0
        total_ERROR = 0

        total_all = 0
        total_mo_all = 0
        total_ed_all = 0
        total_sp_all = 0
        total_na_all = 0

        for pr in self.pr_classifications:
            class_ = self.pr_classifications[pr]['class']
            if os.path.isdir(f"Results/Repos_results/{self.repo_check_number}/{pr}_{class_}") is True:
                shutil.rmtree(f"Results/Repos_results/{self.repo_check_number}/{pr}_{class_}")

            os.rename(f"Results/Repos_results/{self.repo_check_number}/{pr}", f"Results/Repos_results/{self.repo_check_number}/{pr}_{class_}")
            if class_ == 'ED':
                total_ED += 1
            elif class_ == 'MO':
                total_MO += 1
            elif class_ == 'SP':
                total_SP += 1
            elif class_ == 'NA':
                total_NA += 1
            elif class_ == 'CC':
                total_CC += 1
            elif class_ == 'NE':
                total_NE += 1
            elif class_ == 'ERROR':
                total_ERROR += 1

            total_mid = total_MO + total_ED + total_SP
            total_all += total_mid

        total_total = len(self.prs)

        total_mo_all += total_MO
        total_ed_all += total_ED
        total_sp_all += total_SP
        total_na_all += total_NA

        totals_list = [total_MO, total_ED, total_SP, total_CC, total_NE, total_NA, total_ERROR]

        analysis.all_class_bar(totals_list, self.repo_check_number, self.repo_main_line, self.repo_divergent, False)

    def fetchPrData(self):
        destination_sha, self.ct = dataloader.get_variant_sha(self.repo_divergent, self.cut_off_date, self.token_list,
                                                                self.ct)
        self.ct, self.repo_data, req, runtime = dataloader.fetch_pullrequest_data(self.repo_main_line, self.repo_divergent, self.prs,
                                                                       destination_sha, self.token_list, self.ct)

    def get_added_git_files(self, mainline, baseSha, prnum):
        try:
            og_path = os.getcwd()
            os.chdir(mainline)
            command = ["git", "fetch", "origin", f"pull/{prnum}/head"]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            command = ['git', 'diff', '--name-status', baseSha, 'FETCH_HEAD']

            result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
            added_files = []
            renamed_files = {}

            for line in result.stdout.strip().split('\n'):
                if line.startswith('R'):
                    parts = line.strip().split('\t')
                    if len(parts) == 3:
                        renamed_files[parts[1]] = parts[2]

                if line.startswith('A'):
                    parts = line.strip().split('\t')
                    if len(parts) == 2:
                        added_files.append(parts[1])  # file path
            os.chdir(og_path)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return []

        return added_files, renamed_files

    def trace_back_to_origin(self, file, renames):
        reverse_map = {v: k for k, v in renames.items()}
        while file in reverse_map:
            file = reverse_map[file]
        return file

    def trace_forward_to_latest(self, file, renames):
        while file in renames:
            file = renames[file]
        return file

    def get_rename_path(self, filename, mainline, divergent):
        origin = self.trace_back_to_origin(filename, mainline)

        latest = self.trace_forward_to_latest(origin, divergent)

        return origin, latest

    def classify(self):
        print(f'\nStarting classification for {self.repo_main_line}, - , {self.repo_divergent}...')
        fileDebug = open("outputDebug.txt", "w")

        start = time.time()
        outputMO = 0
        outputED = 0
        outputSP = 0
        outputNA = 0
        if os.path.isdir(f"Results/Repos_results/{self.repo_check_number}") is False:
            os.makedirs(f"Results/Repos_results/{self.repo_check_number}")

        for pr_nr in self.repo_data:
            if int(pr_nr) >= 0:
                try:
                    # Create directory to save into
                    if os.path.isdir(f"Results/Repos_results/{self.repo_check_number}/{pr_nr}") is False:
                        os.makedirs(f"Results/Repos_results/{self.repo_check_number}/{pr_nr}")
                    else:
                        shutil.rmtree(f"Results/Repos_results/{self.repo_check_number}/{pr_nr}")
                        os.makedirs(f"Results/Repos_results/{self.repo_check_number}/{pr_nr}")

                    print(f'==================================================', file=fileDebug)
                    print(f'Currently Checking PR: {pr_nr}', file=fileDebug)
                    print(f'Created At: {self.repo_data[pr_nr]["created_at"]}', file=fileDebug)
                    print(f'Merged At: {self.repo_data[pr_nr]["merged_at"]}', file=fileDebug)
                    print(f'Base Sha: {self.repo_data[pr_nr]["base_sha_added"]}', file=fileDebug)
                    print(f'==================================================', file=fileDebug)

                    pr_data_user = open(f"Results/Repos_results/{self.repo_check_number}/{pr_nr}/pr_results.txt", "w")
                    print(f"Classified PR: {pr_nr}", file = pr_data_user)
                    print(f"PR Title: {self.repo_data[pr_nr]['title']}", file = pr_data_user)
                    print(f"PR Description: {self.repo_data[pr_nr]['body']}", file=pr_data_user)
                    print(f"PR Location: {self.repo_data[pr_nr]['html_url']}", file = pr_data_user)
                    print(f"", file = pr_data_user)

                    self.results[pr_nr] = {}
                    mainCheck = self.repo_clones + self.repo_check_number + "/" + self.repo_main_line
                    currentAddedFiles, current_renames = self.get_added_git_files(mainCheck, str(self.repo_data[pr_nr]["base_sha_added"]),
                                                                 str(pr_nr))
                    # 18050
                    reverse_map = {v: k for k, v in current_renames.items()}
                    print(f'Current Added: {currentAddedFiles}', file=fileDebug)
                    print(f'Current Renames: {current_renames}', file=fileDebug)
                    print(f"Added Files in the PR (Skipped)", file=pr_data_user)
                    for addedFiles in currentAddedFiles:
                        print(f"  - {addedFiles}", file=pr_data_user)
                    print(f"Renamed Files in PR:", file=pr_data_user)
                    for key, value in current_renames.items():
                        print(f"  - {key} -> {value}", file=pr_data_user)

                    dup_count = 1
                    checkPercetage = {}
                    for files in self.repo_data[pr_nr]['commits_data']:
                        for file in files:
                            localCheckPercetage = []
                            '''
                                THe next few if statements check if the file is a valid file that GACPD can check
                            '''
                            if os.path.isdir(f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}') is False:
                                os.makedirs(f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}')

                            self.results[pr_nr][file] = {}
                            if file.find(".") < 0:
                                result_mod = {}
                                self.results[pr_nr][file]['results'] = list()
                                result_mod['patchClass'] = 'OTHER EXT'
                                self.results[pr_nr][file]['result'] = result_mod
                                continue

                            file_ext = self.file_extensions_swapped.get("."+file.split('.')[1], "unknown")
                            if file_ext == "unknown":
                                result_mod = {}
                                self.results[pr_nr][file]['results'] = list()
                                result_mod['patchClass'] = 'OTHER EXT'
                                self.results[pr_nr][file]['result'] = result_mod

                                shutil.copytree(
                                    f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}',
                                    f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/CC_EXT/{file.replace("/", "_").replace(".", "_")}')

                                shutil.rmtree(
                                    f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}')
                                continue

                            '''
                                If it is a valid file then we now check
                            '''
                            if len(files[file]) != 0:
                                try:
                                    if file_ext != "unknown":
                                        fileName = ''
                                        fileDir = ''

                                        if len(files[file]) == 1:
                                            fileName = commitloader.file_name(file)
                                            fileDir = commitloader.file_dir(file)
                                            status = files[file][0]['status']
                                        # else:
                                        #     first_commit, last_commit = classifier.getFirstLastCommit(
                                        #         self.repo_data[pr_nr]['commits_data'])
                                        #     fileName = commitloader.file_name(file)
                                        #     fileDir = commitloader.file_dir(file)
                                        #     status = first_commit['status']

                                        new_file_dir = ''
                                        for h in fileDir:
                                            new_file_dir = new_file_dir + h + '/'

                                        if self.ct == 40:
                                            self.ct = 0
                                        print(f"Files in PR: {fileName}",
                                              file=pr_data_user)

                                        destPath = ("Results/Repos_files"+"/"+self.repo_check_number+
                                                    '/' +self.repo_divergent + '/' + new_file_dir+'/'+fileName)

                                        divergent_fileNameForRenamesOrAdditions = new_file_dir + fileName

                                        destPath = os.path.normpath(destPath)
                                        destPath = destPath.replace('\\', '/')

                                        """
                                            Get the file after the patch from the variant1
                                        """
                                        if self.ct == 40:
                                            self.ct = 0

                                        patch_lines = files[file][0]['patch']
                                        patchPath = self.repo_dir_files + self.repo_check_number + '/' + self.repo_main_line + '/' + str(
                                            pr_nr) + '/patches/' + new_file_dir

                                        patchPath = os.path.normpath(patchPath)
                                        patchPath = patchPath.replace('\\', '/')

                                        # print(f"Patch Patch: {patchPath}")

                                        patchName = fileName.split('.')[0]
                                        patchPath, dup_count = classifier.save_patch(patchPath, patchName, patch_lines,
                                                                                     dup_count)
                                        # print(f"Patch Patch: {patchPath}")
                                        # sys.exit()
                                        '''
                                            Now check if the file exists - if it doesn't then check for the renames
                                            If its not a renamed file then immediatly check
                                        '''

                                        shutil.copy(destPath, 'cmp/')
                                        shutil.copy(patchPath, 'src/')
                                        repo_files = patchPath.split('/')

                                        extensionCheck = destPath.split('.')
                                        extension = "java"

                                        if(len(extensionCheck) >2):
                                            extension = extensionCheck[len(extensionCheck)-1]
                                        else:
                                            extension = extensionCheck[1]

                                        mainline_fileNameForRenamesOrAdditions = divergent_fileNameForRenamesOrAdditions.split('.')[0] + "." + extension

                                        print(f"Patch Path: {patchPath}", file=fileDebug)
                                        print(f"Dest Path: {destPath}", file=fileDebug)
                                        print(f"File of Linkedin to check: {divergent_fileNameForRenamesOrAdditions}", file=fileDebug)
                                        print(f"File of Apache to check: {mainline_fileNameForRenamesOrAdditions}", file=fileDebug)

                                        renamedDestPath = False
                                        # Ignores files added in current PR
                                        if mainline_fileNameForRenamesOrAdditions in currentAddedFiles:
                                            result_mod = {}
                                            result_mod['type'] = status.upper()
                                            result_mod['destPath'] = ''
                                            result_mod['patchPath'] = patchPath
                                            result_mod['patchClass'] = 'NA'

                                            try:
                                                shutil.copytree(
                                                    f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}',
                                                    f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/NA_ADDED/{file.replace("/", "_").replace(".", "_")}')

                                                shutil.rmtree(
                                                    f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}')
                                            except Exception as e2:
                                                pass

                                            continue

                                        if divergent_fileNameForRenamesOrAdditions != mainline_fileNameForRenamesOrAdditions:
                                            currentCheck = divergent_fileNameForRenamesOrAdditions

                                            cycleFound = False
                                            for cycle in self.cycles:
                                                if currentCheck in cycle:
                                                    cycleFound = True
                                                    currentCheck = cycle[0]
                                                    renamedDestPath = True

                                            # If a cycle has been found do something else
                                            if cycleFound is True:
                                                destPath = ("Results/Repos_files" + "/" + self.repo_check_number +
                                                            '/' + self.repo_divergent + '/' + currentCheck)
                                                print(f"**************************************************", file=fileDebug)
                                                print(f"Renamed Divergent Path is: {destPath}", file=fileDebug)
                                                print(f"**************************************************", file=fileDebug)
                                            elif mainline_fileNameForRenamesOrAdditions in reverse_map:
                                                originalName, currentDivergentName = self.get_rename_path(reverse_map[mainline_fileNameForRenamesOrAdditions],
                                                                                                          self.renames_mainline,
                                                                                                          self.renames)
                                                if originalName != currentDivergentName:
                                                    destPath = ("Results/Repos_files" + "/" + self.repo_check_number +
                                                        '/' + self.repo_divergent + '/' + currentDivergentName)

                                                    print(f"**************************************************",
                                                          file=fileDebug)
                                                    print(f"Renamed Divergent Path is: {destPath}", file=fileDebug)
                                                    print(f"**************************************************",
                                                          file=fileDebug)
                                                    renamedDestPath = True

                                        self.parse_patch_file(f'src/{repo_files[len(repo_files) - 1]}', f'src', f'{extension}')
                                        tokens_context = [10]
                                        files_context = []
                                        for token in tokens_context:
                                            cmd = self.jscpd_bin() + [
                                                "--pattern", f'*.{extension}',
                                                "--min-tokens",  f'{token}',
                                                "src", "cmp"
                                            ]

                                            out = subprocess.run(
                                                cmd,
                                                text=True,
                                                capture_output=True,
                                                cwd=os.getcwd(),          # or a fixed project root Path
                                                encoding="utf-8",         # ← force UTF-8 decoding
                                                errors="replace",         # ← avoid crashes on stray bytes
                                                # check=True,             # (optional) raise on non-zero exit
                                            )

                                            file_check = open(f'{os.getcwd()}/reports/html/jscpd-report.json')
                                            data_check = json.load(file_check)
                                            file_check.close()

                                            format = self.file_extensions_swapped.get("." + extension)

                                            try:
                                                for checks in data_check["statistics"]["formats"][format][
                                                    "sources"]:
                                                    value = data_check["statistics"]["formats"][format]["sources"][
                                                        checks]["duplicatedTokens"]

                                                    if "context" in checks:
                                                        if value != 0:
                                                            files_context.append("_".join(checks.split("_")[:2]))
                                            except Exception as e2:
                                                pass

                                            self.remove_all_files('reports')

                                        classification = ""
                                        tokens_jscpd = [50,40,30]
                                        MO_total = 0
                                        ED_total = 0
                                        SP_total = 0
                                        for jscpdtoken in tokens_jscpd:
                                            MO_check = 0
                                            ED_check = 0
                                            NA_check = 0

                                            cmd = self.jscpd_bin() + [
                                                "--pattern", f'*.{extension}',
                                                "--min-tokens",  f'{token}',
                                                "src", "cmp"
                                            ]

                                            out = subprocess.run(
                                                cmd,
                                                text=True,
                                                capture_output=True,
                                                cwd=os.getcwd(),          # or a fixed project root Path
                                                encoding="utf-8",         # ← force UTF-8 decoding
                                                errors="replace",         # ← avoid crashes on stray bytes
                                                # check=True,             # (optional) raise on non-zero exit
                                            )

                                            file_check = open(f'{os.getcwd()}/reports/html/jscpd-report.json')
                                            data_check = json.load(file_check)
                                            file_check.close()

                                            mo_context_check = []
                                            ed_context_check = []
                                            format = self.file_extensions_swapped.get("." + extension)
                                            try:
                                                for checks in data_check["statistics"]["formats"][format][
                                                    "sources"]:
                                                    value = data_check["statistics"]["formats"][format]["sources"][
                                                                checks]["duplicatedTokens"]
                                                    if "deletions" in checks:
                                                        MO_check += value
                                                        if value == 0:
                                                            for hunk in files_context:
                                                                if checks.startswith(hunk):
                                                                    mo_context_check.append(checks)
                                                                    break
                                                        percentage = data_check["statistics"]["formats"][format]["sources"][
                                                                checks]["percentage"]
                                                        localCheckPercetage.append(f"{checks} ({jscpdtoken}) - has a similarity of: {percentage}%\n")
                                                    if "additions" in checks:
                                                        ED_check += value
                                                        if value == 0:
                                                            for hunk in files_context:
                                                                if checks.startswith(hunk):
                                                                    ed_context_check.append(checks)
                                                                    break
                                                        percentage = data_check["statistics"]["formats"][format]["sources"][
                                                                checks]["percentage"]
                                                        localCheckPercetage.append(f"{checks} ({jscpdtoken}) - has a similarity of: {percentage}%\n")
                                            except Exception as e3:
                                                print("HERE - 2")

                                            if MO_check == 0 and len(mo_context_check) > 0:
                                                ED_total += 1
                                            elif ED_check == 0 and len(ed_context_check) > 0:
                                                MO_total += 1
                                            elif MO_check == 0 and ED_check == 0:
                                                NA_check += 1
                                                continue
                                            elif MO_check == ED_check:
                                                SP_total += 1
                                                break
                                            elif MO_check > ED_check:
                                                MO_total += 1
                                                break
                                            elif ED_check > MO_check:
                                                ED_total += 1
                                                break

                                        shutil.copytree('src', f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}/src',
                                                        dirs_exist_ok=True)
                                        shutil.copytree('cmp', f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}/cmp',
                                                        dirs_exist_ok=True)
                                        shutil.copytree('reports', f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}/reports',
                                                        dirs_exist_ok=True)

                                        self.remove_all_files('src')
                                        self.remove_all_files('cmp')
                                        self.remove_all_files('reports')

                                        if MO_total == 0 and ED_total == 0 and SP_total == 0:
                                            classification = "NA"
                                            outputNA += 1
                                        elif MO_total != 0:
                                            classification = "MO"
                                            outputMO += 1
                                        else:
                                            classification = "ED"
                                            outputED += 1

                                        result_mod = {}
                                        result_mod['type'] = status.upper()
                                        result_mod['destPath'] = destPath
                                        result_mod['patchPath'] = patchPath
                                        result_mod['patchClass'] = classification

                                        with open(f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}/results.txt', 'w') as f:
                                            f.write(f"In PR: {pr_nr}\n")
                                            f.write(f"Mainline is: {self.repo_main_line}\n")
                                            f.write(f"Divergent Repo is: {self.repo_divergent}\n")
                                            f.write(f"File: {file}\n")
                                            if renamedDestPath is True:
                                                f.write(f"Renamed Divergent Path is: {destPath}\n")
                                            else:
                                                f.write(f"Is called in Divergent Path is: {destPath}\n")
                                            f.write(f"Similarity Check:\n")
                                            for check in localCheckPercetage:
                                                f.write(check)

                                            f.write("Classification: \n")
                                            f.write(f"The final classification is: {classification}\n")

                                        print(f"Similarity analysis for:  {file}", file=pr_data_user)
                                        print(f"  - Overall Classification is: {classification}", file=pr_data_user)
                                        print(f"Hunk Similarity", file=pr_data_user)
                                        for check in localCheckPercetage:
                                            print(f"  - {check}", file=pr_data_user)
                                        print(f"", file=pr_data_user)

                                        shutil.copytree(f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}',
                                                        f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{classification}/{file.replace("/", "_").replace(".", "_")}')

                                        shutil.rmtree(f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}')
                                        self.results[pr_nr][file]['result'] = result_mod

                                    else:
                                        result_mod = {}
                                        result_mod['patchClass'] = 'OTHER EXT'
                                        self.results[pr_nr][file]['result'] = result_mod
                                except Exception as e:
                                    print('Exception thrown is: ', e)
                                    print('File: ', file)
                                    print(os.getcwd())
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                    print(exc_type, fname, exc_tb.tb_lineno)

                                    result_mod = {}
                                    result_mod['patchClass'] = 'ERROR'
                                    self.results[pr_nr][file]['result'] = result_mod

                                    try:
                                        shutil.copytree(
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}',
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/ERROR/{file.replace("/", "_").replace(".", "_")}')

                                        shutil.rmtree(
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}')
                                    except Exception as e2:
                                        pass

                                    self.remove_all_files('src')
                                    self.remove_all_files('cmp')
                                    self.remove_all_files('reports')
                            else:
                                result_mod = {}
                                self.results[pr_nr][file]['results'] = list()
                                if file_ext == "unknown":
                                    result_mod['patchClass'] = 'OTHER EXT'
                                    self.results[pr_nr][file]['result'] = result_mod
                                    try:
                                        shutil.copytree(
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}',
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/CC_EXT/{file.replace("/", "_").replace(".", "_")}')

                                        shutil.rmtree(
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}')
                                    except Exception as e2:
                                        pass
                                else:
                                    result_mod['patchClass'] = 'NOT EXISTING'
                                    self.results[pr_nr][file]['result'] = result_mod
                                    try:
                                        shutil.copytree(
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}',
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/NE/{file.replace("/", "_").replace(".", "_")}')

                                        shutil.rmtree(
                                            f'Results/Repos_results/{self.repo_check_number}/{pr_nr}/{file.replace("/", "_").replace(".", "_")}')
                                    except Exception as e2:
                                        pass

                    print(f"Recommendations: TBO", file=pr_data_user)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)

        self.pr_classifications = totals.final_class(self.results)
        all_counts = totals.count_all_classifications(self.pr_classifications)

        end = time.time()
        duration = end - start

        common.pickleFile(
            self.main_dir_results + self.repo_check_number + '_' + self.repo_main_line.split('/')[0] + '_' + self.repo_main_line.split('/')[
                1] + '_results', [self.results, self.pr_classifications, all_counts, duration])

    def remove_git_folder(self, folder):
        folder_name = folder.replace("\\", "/")

        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)

    def create_git_folder(self, folder, repo_name):
        repo_name = repo_name.replace("\\", "/")
        repo_owner = repo_name.split("/")

        og_path = os.getcwd()
        if os.path.exists(folder+"/"+repo_owner[0] + "/" + repo_owner[1]):
            os.chdir(folder+"/"+repo_owner[0] + "/" + repo_owner[1])
        else:
            os.makedirs(folder+"/"+repo_owner[0] + "/" + repo_owner[1])
            os.chdir(folder+"/"+repo_owner[0] + "/" + repo_owner[1])

        command = [
            "git",
            "clone",
            f'https://github.com/{repo_owner[1]}/{repo_owner[2]}',
        ]

        subprocess.run(command)

        os.chdir(og_path)

    def obtain_git_rename_history(self, start_date, end_date, repo_path):
        og_path = os.getcwd()
        os.chdir(repo_path)

        # Git command to give us the oldest renames first, and then the latests
        # This ensures the dictionary will contain the most recent renames in its value
        command = [
            "git",
            "log",
            "--diff-filter=R",
            "--name-status",
            "--pretty=format:",
            f"--since={start_date}",
            f"--until={end_date}",
            "--reverse"
        ]

        results = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        rename_history = {}
        for line in results.stdout.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) == 3 and parts[0].startswith("R"):
                old_name = parts[1]
                new_name = parts[2]

                rename_history[old_name] = new_name


        os.chdir(og_path)

        return rename_history

    def find_cycle_from_file(self, start, renames, visited):
        path = []
        local_visited = {}

        current = start
        while current in renames:
            if current in local_visited:
                # Cycle detected
                cycle_start_idx = local_visited[current]
                cycle = path[cycle_start_idx:] + [current]
                return cycle
            if current in visited:
                return None
            local_visited[current] = len(path)
            path.append(current)
            current = renames[current]
        return None

    def find_rename_cyles(self, renames):
        visited = set()
        cycles = []

        for file in renames:
            if file not in visited:
                cycle = self.find_cycle_from_file(file, renames, visited)
                if cycle:
                    cycles.append(cycle)
                    visited.update(cycle)

        return cycles

    def obtain_git_information(self):
        repo_name = "Results/Repos_files"+"/"+self.repo_check_number+"/"+self.repo_divergent

        url = f"https://api.github.com/repos/{self.repo_divergent}"

        created_at = ""
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()
            created_at = data.get("created_at")
            if created_at:
                print(f"Repository created at: {created_at}")
            else:
                print("The 'created_at' field is not found in the response.")
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")

        self.renames = self.obtain_git_rename_history(created_at, self.modern_day, repo_name)
        repo_name = "Results/Repos_clones" + "/" + self.repo_check_number + "/" + self.repo_main_line
        self.renames_mainline = self.obtain_git_rename_history(created_at, self.modern_day, repo_name)
        self.cycles = self.find_rename_cyles(self.renames)

    def runClassification(self, prs_source):
        self.set_prs(prs_source)
        self.fetchPrData()

        # # Removes old git clone (if it exists) to ensure we have latest version
        repo_name = self.repo_divergent.split('/')[0]
        self.remove_git_folder("Results/Repos_files"+"/"+self.repo_check_number+"/"+repo_name)
        repo_name = self.repo_main_line.split('/')[0]
        self.remove_git_folder(self.repo_clones + "/" + self.repo_check_number + "/" + repo_name)
        #
        # # clones latest version of repo to ensure we have latest version
        file = self.repo_check_number+"/"+self.repo_divergent
        self.create_git_folder("Results/Repos_files", file)

        file = self.repo_check_number + "/" + self.repo_main_line
        self.create_git_folder(self.repo_clones, file)

        self.obtain_git_information()
        print('======================================================================')
        self.classify()
        self.createDf()
        print('======================================================================')
        self.visualizeResults()

    def dfPatches(self, nr_patches=-1):
        if nr_patches == -1:
            return self.df_patches
        else:
            if nr_patches > self.df_patches.shape[0]:
                print(
                    f'The dataframe contain only {self.df_patches.shape[0]} rows. Printing only {self.df_patches.shape[0]} rows.')
            return self.df_patches.head(nr_patches)

    def dfFileClass(self, nr_patches=-1):
        if nr_patches == -1:
            return self.df_files_classes
        else:
            if nr_patches > self.df_files_classes.shape[0]:
                print(
                    f'The dataframe contain only {self.df_files_classes.shape[0]} rows. Printing only {self.df_files_classes.shape[0]} rows.')
            return self.df_files_classes.head(nr_patches)

    def dfPatchClass(self, nr_patches=-1):
        if nr_patches == -1:
            return self.df_patch_classes
        else:
            if nr_patches > self.df_patch_classes.shape[0]:
                print(
                    f'The dataframe contain only {self.df_patch_classes.shape[0]} rows. Printing only {self.df_patch_classes.shape[0]} rows.')
            return self.df_patch_classes.head(nr_patches)

    def create_dynamic_js(self, output_path="dynamic_boxes.js", target_dir="Results/Repos_results"):
        data = {}

        for folder in os.listdir(target_dir):
            folder_path = os.path.join(target_dir, folder)
            if not os.path.isdir(folder_path): continue

            class_map = defaultdict(dict)
            for sub in os.listdir(folder_path):
                sub_path = os.path.join(folder_path, sub)
                if os.path.isdir(sub_path) and "_" in sub:
                    prefix, classification = sub.rsplit("_", 1)
                    pr_info = {
                        "path": f"{folder}/{sub}",
                        "subfolders": [],
                        "has_summary": os.path.exists(os.path.join(sub_path, "pr_results.txt"))
                    }

                    for child in os.listdir(sub_path):
                        full = os.path.join(sub_path, child)
                        if os.path.isdir(full):
                            sub_subs = [gchild for gchild in os.listdir(full) if
                                        os.path.isdir(os.path.join(full, gchild))]
                            pr_info["subfolders"].append({
                                "name": child,
                                "subfolders": sub_subs
                            })

                    class_map[classification].setdefault("prs", {})[prefix] = pr_info

            data[folder] = {k: v for k, v in class_map.items()}

        js_data = json.dumps(data)
        base_dir = target_dir.replace("\\", "/")

        with open(output_path, "w") as f:
            f.write(f"""
        document.addEventListener("DOMContentLoaded", function () {{
            const data = {js_data};
            const baseDir = "{base_dir}";

            const body = document.body;
            const container = document.createElement("div");
            const backButton = document.createElement("button");

            body.style.margin = "0";
            body.style.fontFamily = "Arial, sans-serif";
            container.style.padding = "20px";
            container.style.paddingTop = "80px";
            body.appendChild(container);

            backButton.textContent = "<- Back";
            Object.assign(backButton.style, {{
                position: "absolute",
                top: "20px",
                left: "20px",
                padding: "10px 15px",
                fontSize: "16px",
                cursor: "pointer",
                display: "none"
            }});
            body.appendChild(backButton);

            let navStack = [];

            function goBack() {{
                if (navStack.length > 0) {{
                    const last = navStack.pop();
                    last();
                }}
                if (navStack.length === 0) backButton.style.display = "none";
            }}
            backButton.onclick = goBack;

            function setCenteredLayout() {{
                container.style.display = "flex";
                container.style.flexWrap = "wrap";
                container.style.justifyContent = "center";
                container.style.alignItems = "center";
            }}

            function setListLayout() {{
                container.style.display = "block";
                container.style.maxWidth = "800px";
                container.style.margin = "auto";
            }}

            function boxStyle() {{
                return {{
                    width: "200px",
                    height: "120px",
                    backgroundColor: "#fff",
                    border: "1px solid #ddd",
                    borderRadius: "10px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: "600",
                    fontSize: "16px",
                    margin: "10px",
                    cursor: "pointer",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.05)"
                }};
            }}

            function buttonStyle() {{
                return {{
                    padding: "12px 24px",
                    fontSize: "16px",
                    margin: "10px",
                    backgroundColor: "#2563eb",
                    color: "#fff",
                    border: "none",
                    borderRadius: "8px",
                    cursor: "pointer",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
                }};
            }}

            function renderPage1_RepoButtons() {{
                container.innerHTML = "";
                setCenteredLayout();
                Object.keys(data).forEach(repo => {{
                    const box = document.createElement("div");
                    box.textContent = repo;
                    Object.assign(box.style, boxStyle());
                    box.onclick = () => {{
                        navStack.push(renderPage1_RepoButtons);
                        renderPage2_ClassificationButtons(repo);
                        backButton.style.display = "block";
                    }};
                    container.appendChild(box);
                }});
            }}

            function renderPage2_ClassificationButtons(repo) {{
                container.innerHTML = "";
                setCenteredLayout();
                Object.keys(data[repo]).forEach(classification => {{
                    const btn = document.createElement("button");
                    btn.textContent = classification;
                    Object.assign(btn.style, buttonStyle());
                    btn.onclick = () => {{
                        navStack.push(() => renderPage2_ClassificationButtons(repo));
                        renderPage3_PRList(repo, classification);
                    }};
                    container.appendChild(btn);
                }});
            }}

            function renderPage3_PRList(repo, classification) {{
                container.innerHTML = "";
                setListLayout();

                const input = document.createElement("input");
                input.type = "text";
                input.placeholder = "Search PR...";
                Object.assign(input.style, {{
                    width: "100%",
                    padding: "12px",
                    fontSize: "16px",
                    marginBottom: "20px",
                    border: "1px solid #ccc",
                    borderRadius: "6px"
                }});
                container.appendChild(input);

                const list = document.createElement("ul");
                list.style.listStyleType = "none";
                list.style.padding = "0";
                container.appendChild(list);

                function updateList(filter = "") {{
                    list.innerHTML = "";
                    const prs = data[repo][classification]["prs"];
                    Object.keys(prs).filter(pr => pr.toLowerCase().includes(filter.toLowerCase())).sort().forEach(pr => {{
                        const li = document.createElement("li");
                        li.textContent = pr;
                        li.style.cursor = "pointer";
                        li.style.padding = "10px";
                        li.style.borderBottom = "1px solid #eee";
                        li.onclick = () => {{
                            navStack.push(() => renderPage3_PRList(repo, classification));
                            renderPage4_PRDetails(repo, classification, pr);
                        }};
                        list.appendChild(li);
                    }});
                }}

                input.addEventListener("input", () => updateList(input.value));
                updateList();
            }}

            function renderPage4_PRDetails(repo, classification, pr) {{
                container.innerHTML = "";
                setListLayout();

                const prData = data[repo][classification]["prs"][pr];

                const heading = document.createElement("h2");
                heading.textContent = "Subfolders for PR " + pr;
                heading.style.marginBottom = "20px";
                container.appendChild(heading);

                if (prData["has_summary"]) {{
                    const summaryBtn = document.createElement("button");
                    summaryBtn.textContent = "Summary (pr_results.txt)";
                    Object.assign(summaryBtn.style, buttonStyle());
                    summaryBtn.onclick = () => {{
                        navStack.push(() => renderPage4_PRDetails(repo, classification, pr));
                        renderPage5_Summary(prData.path);
                    }};
                    container.appendChild(summaryBtn);
                }}

                const list = document.createElement("ul");
                list.style.listStyleType = "none";
                list.style.padding = "0";
                list.style.marginTop = "20px";

                prData.subfolders.sort((a, b) => a.name.localeCompare(b.name)).forEach(sub => {{
                    const li = document.createElement("li");
                    li.textContent = sub.name;
                    li.style.cursor = "pointer";
                    li.style.padding = "10px";
                    li.style.borderBottom = "1px solid #eee";
                    li.onclick = () => {{
                        navStack.push(() => renderPage4_PRDetails(repo, classification, pr));
                        renderPage6_SubfolderDetails(repo, classification, pr, sub.name, sub.subfolders);
                    }};
                    list.appendChild(li);
                }});

                container.appendChild(list);
            }}

            function renderPage5_Summary(prPath) {{
                container.innerHTML = "";
                setListLayout();

                const heading = document.createElement("h2");
                heading.textContent = "Summary File Contents";
                heading.style.marginBottom = "20px";
                container.appendChild(heading);

                const contentBox = document.createElement("pre");
                contentBox.style.padding = "15px";
                contentBox.style.backgroundColor = "#f8f8f8";
                contentBox.style.border = "1px solid #ccc";
                contentBox.style.whiteSpace = "pre-wrap";
                contentBox.style.maxWidth = "100%";
                contentBox.style.overflowX = "auto";
                container.appendChild(contentBox);

                const filePath = baseDir + "/" + prPath + "/pr_results.txt";
                fetch(filePath)
                    .then(resp => resp.text())
                    .then(text => {{
                        contentBox.textContent = text;
                    }})
                    .catch(() => {{
                        contentBox.textContent = "Failed to load pr_results.txt";
                    }});
            }}

function renderPage6_SubfolderDetails(repo, classification, pr, folderName, subfolderList) {{
    container.innerHTML = "";
    setListLayout();

    const heading = document.createElement("h2");
    heading.textContent = `Contents of ${{folderName}}`;
    heading.style.marginBottom = "20px";
    container.appendChild(heading);

    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Search subfolders...";
    Object.assign(input.style, {{
        width: "100%",
        padding: "12px",
        fontSize: "16px",
        marginBottom: "20px",
        border: "1px solid #ccc",
        borderRadius: "6px"
    }});
    container.appendChild(input);

    const list = document.createElement("ul");
    list.style.listStyleType = "none";
    list.style.padding = "0";
    container.appendChild(list);

    function updateList(filter = "") {{
        list.innerHTML = "";
        const filtered = subfolderList.filter(name =>
            name.toLowerCase().includes(filter.toLowerCase())
        ).sort();

        if (filtered.length === 0) {{
            const emptyMsg = document.createElement("li");
            emptyMsg.textContent = "No matching subfolders.";
            emptyMsg.style.padding = "10px";
            emptyMsg.style.color = "#888";
            list.appendChild(emptyMsg);
        }}

        filtered.forEach(name => {{
            const li = document.createElement("li");
            li.textContent = name;
            li.style.cursor = "pointer";
            li.style.padding = "10px";
            li.style.borderBottom = "1px solid #eee";

            li.onclick = () => {{
                const path = `${{baseDir}}/${{data[repo][classification]["prs"][pr].path}}/${{folderName}}/${{name}}/reports/html/index.html`;
                window.open(path, "_blank");
            }};

            list.appendChild(li);
        }});
    }}

    input.addEventListener("input", () => updateList(input.value));
    updateList();
}}

            renderPage1_RepoButtons();
        }});
        """)

        print(f"✅ JavaScript file written to: {output_path}")

    def get_git_information(self):
        # # Removes old git clone (if it exists) to ensure we have latest version
        repo_name = self.repo_divergent.split('/')[0]
        self.remove_git_folder("Results/Repos_files"+"/"+self.repo_check_number+"/"+repo_name)
        repo_name = self.repo_main_line.split('/')[0]
        self.remove_git_folder(self.repo_clones + "/" + self.repo_check_number + "/" + repo_name)
        #
        # # clones latest version of repo to ensure we have latest version
        file = self.repo_check_number+"/"+self.repo_divergent
        self.create_git_folder("Results/Repos_files", file)

        file = self.repo_check_number + "/" + self.repo_main_line
        self.create_git_folder(self.repo_clones, file)

        self.obtain_git_information()

    def individual_pr_check(self, pr_number):
        try:
            if os.path.isdir(f"Results/Repos_results/{self.repo_check_number}") is False:
                os.makedirs(f"Results/Repos_results/{self.repo_check_number}")

            # Create directory to save into
            if os.path.isdir(f"Results/Repos_results/{self.repo_check_number}/{pr_number}") is False:
                os.makedirs(f"Results/Repos_results/{self.repo_check_number}/{pr_number}")
            else:
                shutil.rmtree(f"Results/Repos_results/{self.repo_check_number}/{pr_number}")
                os.makedirs(f"Results/Repos_results/{self.repo_check_number}/{pr_number}")
        except Exception as e:
            pass

        # Obtains specific PR
        if self.ct == len(self.token_list):
            self.ct = 0

        pr_request = f'{constant.GITHUB_API_BASE_URL}{self.repo_main_line}/pulls/{pr_number}'
        pr = helpers.api_request(pr_request, self.token_list[self.ct])
        self.ct += 1

        mainCheck = self.repo_clones + self.repo_check_number + "/" + self.repo_main_line
        currentAddedFiles, current_renames = self.get_added_git_files(mainCheck,
                                                                      str(pr['base']['sha']),
                                                                      str(pr_number))
        self.prs = [pr_number]
        destination_sha, self.ct = dataloader.get_variant_sha(self.repo_divergent, self.cut_off_date, self.token_list,
                                                                self.ct)
        self.ct, self.repo_data, req, runtime = dataloader.fetch_pullrequest_data(self.repo_main_line, self.repo_divergent, self.prs,
                                                                       destination_sha, self.token_list, self.ct)

        self.classify()
