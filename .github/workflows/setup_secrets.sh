__doc__="
Development script for updating secrets when they rotate
"

cd $HOME/code/line_profiler

# Load or generate secrets
source $(secret_loader.sh)
echo $PYUTILS_TWINE_USERNAME
CI_SECRET=$PYUTILS_CI_GITHUB_SECRET
echo "CI_SECRET = $CI_SECRET"

# ADD RELEVANT VARIABLES TO THE CI SECRET VARIABLES

# HOW TO ENCRYPT YOUR SECRET GPG KEY
# You need to have a known public gpg key for this to make any sense
IDENTIFIER="travis-ci-Erotemic"
GPG_KEYID=$(gpg --list-keys --keyid-format LONG "$IDENTIFIER" | head -n 2 | tail -n 1 | awk '{print $1}' | tail -c 9)
echo "GPG_KEYID = $GPG_KEYID"

# Export plaintext gpg public keys, private keys, and trust info
mkdir -p dev
gpg --armor --export-secret-keys $GPG_KEYID > dev/ci_secret_gpg_key.pgp
gpg --armor --export $GPG_KEYID > dev/ci_public_gpg_key.pgp
gpg --export-ownertrust > dev/gpg_owner_trust

# Encrypt gpg keys and trust with CI secret
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -e -a -in dev/ci_public_gpg_key.pgp > dev/ci_public_gpg_key.pgp.enc
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -e -a -in dev/ci_secret_gpg_key.pgp > dev/ci_secret_gpg_key.pgp.enc
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -e -a -in dev/gpg_owner_trust > dev/gpg_owner_trust.enc
echo $GPG_KEYID > dev/public_gpg_key

# Test decrpyt
cat dev/public_gpg_key
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_public_gpg_key.pgp.enc 
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/gpg_owner_trust.enc 
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_secret_gpg_key.pgp.enc 

source $(secret_unloader.sh)

# Look at what we did, clean up, and add it to git
ls dev/*.enc
rm dev/gpg_owner_trust dev/*.pgp
git status
git add dev/*.enc
git add dev/public_gpg_key
