Vagrant
-------

While some testing and building needs to be done on the target platform A64 some tasks (like building OpenWRT etc) are performed on 'regular' amd64.
For this we use Vagrant boxes, which we provision using ansible playbooks.

For some playbooks we require the ansible vault feature, unfortunately vagrant only supports this when provided with a plaintext file containing the password.

To this end you can either create a file named ``.vault_password_file`` and paste the contents from your keyring or paste the output from gpg like so: ``gpg -d ../../nuimo-infrastructure/etc/tom@senic.com.key.gpg  > .vault_password_file``