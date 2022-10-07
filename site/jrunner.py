import subprocess
from time import sleep


# JOB RUNNER CONSTANTS
JOB_PATH = '/home/marthinus/projects/studies/ai_art/stabledif/stable-diffusion'


def job_generate(task_prompt, task_id, task_sessionid, task_dir, task_samples, task_H, task_W, task_steps, task_scale, task_seed):
    '''Run Generation Job'''
    subprocess.run(['pipenv', 'run', 'python', 'optimizedSD/optimized_txt2img_dd.py', '--sessionid', task_sessionid, '--taskid', task_id, '--prompt', task_prompt, '--outdir', task_dir, '--n_samples', task_samples, '--H', task_H, '--W', task_W, '--ddim_steps', task_steps, '--scale', task_scale, '--seed', task_seed], cwd=JOB_PATH)


def job_variance(task_prompt, task_id, task_sessionid, task_input, task_dir, task_samples, task_H, task_W, task_steps, task_scale, task_seed):
    '''Run Variance Job'''
    subprocess.run(['pipenv', 'run', 'python', 'optimizedSD/optimized_img2img_dd.py', '--sessionid', task_sessionid, '--taskid', task_id, '--prompt', task_prompt, '--init-img', task_input ,'--outdir', task_dir, '--n_samples', task_samples, '--H', task_H, '--W', task_W, '--ddim_steps', task_steps, '--scale', task_scale, '--seed', task_seed], cwd=JOB_PATH)
