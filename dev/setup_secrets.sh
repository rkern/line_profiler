__doc__='
============================
SETUP CI SECRET INSTRUCTIONS
============================

TODO: These instructions are currently pieced together from old disparate
instances, and are not yet fully organized.

The original template file should be:
~/misc/templates/PYPKG/dev/setup_secrets.sh

Development script for updating secrets when they rotate


The intent of this script is to help setup secrets for whichever of the
following CI platforms is used:

../.github/workflows/tests.yml
../.gitlab-ci.yml
../.circleci/config.yml


=========================
GITHUB ACTION INSTRUCTIONS
=========================

* `PERSONAL_GITHUB_PUSH_TOKEN` - 
    This is only needed if you want to automatically git-tag release branches.

    To make a API token go to:
        https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token


=========================
GITLAB ACTION INSTRUCTIONS
=========================

    ```bash
    cat .setup_secrets.sh | \
        sed "s|utils|<YOUR-GROUP>|g" | \
        sed "s|PYPKG|<YOUR-REPO>|g" | \
        sed "s|travis-ci-Erotemic|<YOUR-GPG-ID>|g" | \
        sed "s|CI_SECRET|<YOUR_CI_SECRET>|g" | \
        sed "s|GITLAB_ORG_PUSH_TOKEN|<YOUR_GIT_ORG_PUSH_TOKEN>|g" | \
        sed "s|gitlab.org.com|gitlab.your-instance.com|g" | \
    tee /tmp/repl && colordiff .setup_secrets.sh /tmp/repl
    ```

    * Make sure you add Runners to your project 
    https://gitlab.org.com/utils/PYPKG/-/settings/ci_cd 
    in Runners-> Shared Runners
    and Runners-> Available specific runners

    * Ensure that you are auto-cancel redundant pipelines.
    Navigate to https://gitlab.kitware.com/utils/PYPKGS/-/settings/ci_cd and ensure "Auto-cancel redundant pipelines" is checked.

    More details are here https://docs.gitlab.com/ee/ci/pipelines/settings.html#auto-cancel-redundant-pipelines

    * TWINE_USERNAME - this is your pypi username
        twine info is only needed if you want to automatically publish to pypi

    * TWINE_PASSWORD - this is your pypi password 

    * CI_SECRET - We will use this as a secret key to encrypt/decrypt gpg secrets 
        This is only needed if you want to automatically sign published
        wheels with a gpg key.

    * GITLAB_ORG_PUSH_TOKEN - 
        This is only needed if you want to automatically git-tag release branches.

        Create a new personal access token in User->Settings->Tokens, 
        You can name the token GITLAB_ORG_PUSH_TOKEN_VALUE
        Give it api and write repository permissions

        SeeAlso: https://gitlab.org.com/profile/personal_access_tokens

        Take this variable and record its value somewhere safe. I put it in my secrets file as such:

            export GITLAB_ORG_PUSH_TOKEN_VALUE=<paste-the-value-here>

        I also create another variable with the prefix "git-push-token", which is necessary

            export GITLAB_ORG_PUSH_TOKEN=git-push-token:$GITLAB_ORG_PUSH_TOKEN_VALUE

        Then add this as a secret variable here: https://gitlab.org.com/groups/utils/-/settings/ci_cd
        Note the value of GITLAB_ORG_PUSH_TOKEN will look something like: "{token-name}:{token-password}"
        For instance it may look like this: "git-push-token:62zutpzqga6tvrhklkdjqm"

        References:
            https://stackoverflow.com/questions/51465858/how-do-you-push-to-a-gitlab-repo-using-a-gitlab-ci-job

     # ADD RELEVANT VARIABLES TO GITLAB SECRET VARIABLES
     # https://gitlab.kitware.com/computer-vision/kwcoco/-/settings/ci_cd
     # Note that it is important to make sure that these variables are
     # only decrpyted on protected branches by selecting the protected
     # and masked option. Also make sure you have master and release
     # branches protected.
     # https://gitlab.kitware.com/computer-vision/kwcoco/-/settings/repository#js-protected-branches-settings


============================
Relevant CI Secret Locations
============================

https://github.com/pyutils/line_profiler/settings/secrets/actions

https://app.circleci.com/settings/project/github/pyutils/line_profiler/environment-variables?return-to=https%3A%2F%2Fapp.circleci.com%2Fpipelines%2Fgithub%2Fpyutils%2Fline_profiler
'


setup_package_environs(){
    __doc__="
    Setup environment variables specific for this project.
    The remainder of this script should ideally be general to any repo.  These
    non-secret variables are written to disk and loaded by the script, such
    that the specific repo only needs to modify that configuration file.
    "

    #echo '
    #export VARNAME_CI_SECRET="CI_KITWARE_SECRET"
    #export GPG_IDENTIFIER="=Erotemic-CI <erotemic@gmail.com>"
    #' | python -c "import sys; from textwrap import dedent; print(dedent(sys.stdin.read()).strip(chr(10)))" > dev/secrets_configuration.sh

    echo '
    export VARNAME_CI_SECRET="PYUTILS_CI_SECRET"
    export GPG_IDENTIFIER="=PyUtils-CI <openpyutils@gmail.com>"
    ' | python -c "import sys; from textwrap import dedent; print(dedent(sys.stdin.read()).strip(chr(10)))" > dev/secrets_configuration.sh
}


export_encrypted_code_signing_keys(){
    # You will need to rerun this whenever the signkeys expire and are renewed

    # Load or generate secrets
    load_secrets

    source dev/secrets_configuration.sh

    CI_SECRET="${!VARNAME_CI_SECRET}"
    echo "CI_SECRET=$CI_SECRET"
    echo "GPG_IDENTIFIER=$GPG_IDENTIFIER"

    # ADD RELEVANT VARIABLES TO THE CI SECRET VARIABLES

    # HOW TO ENCRYPT YOUR SECRET GPG KEY
    # You need to have a known public gpg key for this to make any sense

    MAIN_GPG_KEYID=$(gpg --list-keys --keyid-format LONG "$GPG_IDENTIFIER" | head -n 2 | tail -n 1 | awk '{print $1}')
    GPG_SIGN_SUBKEY=$(gpg --list-keys --with-subkey-fingerprints "$GPG_IDENTIFIER" | grep "\[S\]" -A 1 | tail -n 1 | awk '{print $1}')
    echo "MAIN_GPG_KEYID  = $MAIN_GPG_KEYID"
    echo "GPG_SIGN_SUBKEY = $GPG_SIGN_SUBKEY"

    # Only export the signing secret subkey 
    # Export plaintext gpg public keys, private sign key, and trust info
    mkdir -p dev
    gpg --armor --export-options export-backup --export-secret-subkeys "${GPG_SIGN_SUBKEY}!" > dev/ci_secret_gpg_subkeys.pgp
    gpg --armor --export ${GPG_SIGN_SUBKEY} > dev/ci_public_gpg_key.pgp
    gpg --export-ownertrust > dev/gpg_owner_trust

    # Encrypt gpg keys and trust with CI secret
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -e -a -in dev/ci_public_gpg_key.pgp > dev/ci_public_gpg_key.pgp.enc
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -e -a -in dev/ci_secret_gpg_subkeys.pgp > dev/ci_secret_gpg_subkeys.pgp.enc
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -e -a -in dev/gpg_owner_trust > dev/gpg_owner_trust.enc
    echo $GPG_KEYID > dev/public_gpg_key

    # Test decrpyt
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_public_gpg_key.pgp.enc | gpg --list-packets --verbose
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_secret_gpg_subkeys.pgp.enc  | gpg --list-packets --verbose
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/gpg_owner_trust.enc | gpg --list-packets --verbose
    cat dev/public_gpg_key

    unload_secrets

    # Look at what we did, clean up, and add it to git
    ls dev/*.enc
    rm dev/*.pgp
    rm dev/gpg_owner_trust
    git status
    git add dev/*.enc
    git add dev/gpg_owner_trust
    git add dev/public_gpg_key
}


_test_gnu(){
    export GNUPGHOME=$(mktemp -d -t)
    ls -al $GNUPGHOME
    chmod 700 -R $GNUPGHOME

    source dev/secrets_configuration.sh

    gpg -k
    
    load_secrets
    CI_SECRET="${!VARNAME_CI_SECRET}"
    echo "CI_SECRET = $CI_SECRET"

    cat dev/public_gpg_key
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_public_gpg_key.pgp.enc 
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_secret_gpg_subkeys.pgp.enc

    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_public_gpg_key.pgp.enc | gpg --import
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_secret_gpg_subkeys.pgp.enc | gpg --import

    gpg -k
    # | gpg --import
    # | gpg --list-packets --verbose
}

