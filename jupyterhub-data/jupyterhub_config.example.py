# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Configuration file for JupyterHub
import os
import json
from dockerspawner import DockerSpawner

class DockerFormSpawner(DockerSpawner):

    # relies on HTML5 for image datalist
    def _options_form_default(self):
        return '''
    <label for='image'>Image</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <input list="image" name="image" placeholder='repo/image:tag' class="form-control">
    <datalist id="image">
      <option value="eisenxu/tensorflow-1.7.0-notebook-cpu:v20180419-0ad94c4e">
      <option value="eisenxu/tensorflow-1.7.0-notebook-gpu:v20180419-0ad94c4e">
    </datalist>
    <br/><br/>

    <label for='cpu_guarantee'>CPU</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <input name='cpu_guarantee' placeholder='200m, 1.0, 2.5, etc' class='form-control'></input>
    <br/><br/>

    <label for='mem_guarantee'>Memory</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <input name='mem_guarantee' placeholder='100Mi, 1.5Gi' class='form-control'></input>
    <br/><br/>

    <label for='extra_resource_limits'>Extra Resource Limits</label>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <input name='extra_resource_limits' placeholder='{&quot;nvidia.com/gpu&quot;: 3}' class='form-control'></input>
    <br/><br/>
    '''

    def options_from_form(self, formdata):
        options = {}
        options['image'] = formdata.get('image', [''])[0].strip()
        options['cpu_guarantee'] = formdata.get(
            'cpu_guarantee', [''])[0].strip()
        options['mem_guarantee'] = formdata.get(
            'mem_guarantee', [''])[0].strip()
        options['extra_resource_limits'] = formdata.get(
            'extra_resource_limits', [''])[0].strip()
        return options

    @property
    def image(self):
        image = 'eisenxu/tensorflow-notebook-cpu'
        if self.user_options.get('image'):
            image = self.user_options['image']
        return image

    @property
    def cpu_guarantee(self):
        cpu = '500m'
        if self.user_options.get('cpu_guarantee'):
            cpu = self.user_options['cpu_guarantee']
        return cpu

    @property
    def mem_guarantee(self):
        mem = '1Gi'
        if self.user_options.get('mem_guarantee'):
            mem = self.user_options['mem_guarantee']
        return mem

    @property
    def extra_resource_limits(self):
        extra = ''
        if self.user_options.get('extra_resource_limits'):
            extra = json.loads(self.user_options['extra_resource_limits'])
        return extra


c = get_config()


# We rely on environment variables to configure JupyterHub so that we
# avoid having to rebuild the JupyterHub container every time we change a
# configuration parameter.

c.JupyterHub.ip = '0.0.0.0'

# Spawn single-user servers as Docker containers
c.JupyterHub.spawner_class = DockerFormSpawner
# Spawn containers from this image
# c.DockerSpawner.container_image = os.environ['DOCKER_NOTEBOOK_IMAGE']
# JupyterHub requires a single-user instance of the Notebook server, so we
# default to using the `start-singleuser.sh` script included in the
# jupyter/docker-stacks *-notebook images as the Docker run command when
# spawning containers.  Optionally, you can override the Docker run command
# using the DOCKER_SPAWN_CMD environment variable.
spawn_cmd = os.environ.get('DOCKER_SPAWN_CMD', "start-singleuser.sh")
c.DockerSpawner.extra_create_kwargs.update({ 'command': spawn_cmd })
# Connect containers to this Docker network
network_name = os.environ['DOCKER_NETWORK_NAME']
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name
# Pass the network name as argument to spawned containers
c.DockerSpawner.extra_host_config = { 'network_mode': network_name }
# Explicitly set notebook directory because we'll be mounting a host volume to
# it.  Most jupyter/docker-stacks *-notebook images run the Notebook server as
# user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
# We follow the same convention.
notebook_dir = os.environ.get('DOCKER_NOTEBOOK_DIR') or '/home/jovyan/work'
c.DockerSpawner.notebook_dir = notebook_dir
# c.DockerSpawner.default_url = "/tree%s" % notebook_dir
# Mount the real user's Docker volume on the host to the notebook user's
# notebook directory in the container
c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': notebook_dir,
    '/tmp/test': { 'bind': '/home/jovyan/data', 'mode': 'ro' }
}
# volume_driver is no longer a keyword argument to create_container()
# c.DockerSpawner.extra_create_kwargs.update({ 'volume_driver': 'local' })
# Remove containers once they are stopped
c.DockerSpawner.remove_containers = True
# For debugging arguments passed to spawned containers
c.DockerSpawner.debug = True

# User containers will access hub by container name on the Docker network
c.JupyterHub.hub_ip = 'jupyterhub'
c.JupyterHub.hub_port = 8080

# Authenticate users with GitHub OAuth
c.JupyterHub.authenticator_class = 'oauthenticator.GitHubOAuthenticator'
c.GitHubOAuthenticator.oauth_callback_url = os.environ['OAUTH_CALLBACK_URL']

# Whitlelist users and admins
c.Authenticator.whitelist = whitelist = set()
c.Authenticator.admin_users = admin = set()
c.JupyterHub.admin_access = True
pwd = os.path.dirname(__file__)
with open(os.path.join(pwd, 'userlist')) as f:
    for line in f:
        if not line:
            continue
        parts = line.split()
        name = parts[0]
        whitelist.add(name)
        if len(parts) > 1 and parts[1] == 'admin':
            admin.add(name)
