"""Trial of the particle filter in TensorFlow Probability.
"""
import os
import time

import matplotlib.pyplot as plt
import numpy as np
import xspec
import seaborn as sns

import tensorflow as tf
import tensorflow_probability as tfp
from tensorflow_probability import bijectors as tfb
from tensorflow_probability import distributions as tfd

import partical_xspec as px


sns.set_style("whitegrid")

tfp_exp = tfp.experimental


def join_and_create_directory(a, *paths, exist_ok=True):
    file_path = os.path.join(a, *paths)
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=exist_ok)
    return file_path


def xspec_settings():
    # Parameter settings.
    enery_kev_start = 0.5
    enery_kev_end = 10.0
    num_bands = 10

    # Model settings.
    xspec.AllModels.setEnergies(
        f"{enery_kev_start} {enery_kev_end} {num_bands}")


def main():

    dtype = tf.float32
    num_particles = 1000

    blockwise_bijector = tfb.Blockwise(
        bijectors=[tfb.Chain([tfb.Scale(1.0), tfb.Exp()]),
                   tfb.Chain([tfb.Scale(10.), tfb.Exp()])]
    )

    transition_function = px.get_transition_function_varmodel(
        coefficients=np.tile(np.diag([0.1, 0.1]), (1, 1, 1)),
        noise_covariance=np.diag(
            tf.convert_to_tensor([0.1, 0.1], dtype=dtype)),
        dtype=dtype)

    observation_function = px.get_observaton_function_xspec_poisson(
        "powerlaw", num_particles, blockwise_bijector)

    initial_state_prior = tfd.MultivariateNormalDiag(
        loc=tf.constant([0.1, 0.1], dtype=dtype),
        scale_diag=tf.constant([0.01, 0.01], dtype=dtype))

    xspec_settings()

    observations = tf.convert_to_tensor(
        np.loadtxt(".cache/observations.txt"),
        dtype=dtype)

    t0 = time.time()
    particles, _, _, log_lik = tfp_exp.mcmc.particle_filter(
        observations,
        initial_state_prior,
        transition_function,
        observation_function,
        num_particles,
        parallel_iterations=1,
        seed=0
    )
    t1 = time.time()
    print("Inference ran in {:.2f}s.".format(t1-t0))

    particles = np.array([1.0, 10.]) * np.exp(particles)

    y_centers = np.quantile(particles, 0.5, axis=-2)

    latents = np.loadtxt(".cache/latents.txt")
    times = np.arange(latents.shape[0])
    fig, ax = plt.subplots(2, sharex=True)
    ax[0].plot(times, latents[:, 0], color="k")
    ax[1].plot(times, latents[:, 1], color="k")
    ax[0].plot(times, y_centers[:, 0], color="r")
    ax[1].plot(times, y_centers[:, 1], color="r")

    errors_sigma_1 = np.quantile(particles, [0.160, 0.840], axis=-2)
    errors_sigma_2 = np.quantile(particles, [0.025, 0.975], axis=-2)
    errors_sigma_3 = np.quantile(particles, [0.001, 0.999], axis=-2)
    for i in range(2):
        common_kw = dict(facecolor="none", color="r", edgecolor="none")
        ax[i].fill_between(times, *errors_sigma_1[..., i], alpha=0.20,
                           **common_kw)
        ax[i].fill_between(times, *errors_sigma_2[..., i], alpha=0.20,
                           **common_kw)
        ax[i].fill_between(times, *errors_sigma_3[..., i], alpha=0.20,
                           **common_kw)

    ax[-1].set_xlabel("Time")
    ax[0].set_ylabel("powerlaw.PhoIndex")
    ax[1].set_ylabel("powerlaw.norm")
    fig.align_ylabels()
    plt.tight_layout()

    savepath = join_and_create_directory(
        ".cache", "figs", "curve_particle_filtered.png")
    plt.savefig(savepath, dpi=150)
    plt.show()
    plt.close()


if __name__ == "__main__":
    main()
