import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from IPython.display import HTML
from scipy.integrate import solve_ivp
from scipy import stats
from pathlib import Path

def recurrence_periods(N, alpha, A):
    
    return 3 / np.pi**(3/2) / np.sqrt(2) * N**(3/2) / np.sqrt(A * alpha)

def plot_oscillation_multiple(results, colors, fname):
    
    grids = {}
    sizes = {}
    matrices = {}
    n_frames = np.inf
    
    for key, res in results.items():
        n_frames = min(len(res.t), n_frames)
        sizes[key] = res.y.shape[0] // 2
        grids[key] = np.arange(sizes[key])
        
    fig, axs = plt.subplots(1, 1, figsize=(16/2,9/2))

    ax_string = axs
    
    lines = {}
    for name, res in results.items():
        line, = ax_string.plot([],[],colors[name],ms=5)
        lines[name] = line

    ax_string.set_xlim(0, sizes[key])
    ax_string.set_ylim(-1.1, 1.1)
    

    def plot_frame(i):
        for name in results:

            lines[name].set_data(grids[name], results[name].y[:sizes[key], i])

    anim = animation.FuncAnimation(
        fig, 
        plot_frame, 
        frames=n_frames, 
        interval=1000/60,
        blit=True,
    )
    anim.save(fname)

def plot_oscillation_and_energy(result, color, fname, label):
    
    n_frames = len(result.t)
    size = result.y.shape[0] // 2
    grid = np.arange(size)
    
    i = np.arange(size)
    N = size-1
    matrix = np.sqrt(2/N) * np.sin(i[:, np.newaxis] * i[np.newaxis, :] * np.pi / N)
    
    omegas = 2 * np.sin(np.pi * i / 2 / N)
    t_1 = 2 * np.pi / omegas[1]

    def get_energies(yyp):
        Qp = matrix @ yyp[:size]
        Qk = matrix @ yyp[size:]
        
        return .5 * Qk**2, .5 * omegas**2 * Qp**2

    fig, axs = plt.subplots(1, 2, figsize=(16/2, 9/2))

    ax_string = axs[0]
    ax_energy = axs[1]

    line, = ax_string.plot([],[],color,ms=5)
    bars_k = ax_energy.bar(grid, np.zeros_like(grid), color=color, alpha=.5, label='Kinetic energy')
    bars_p = ax_energy.bar(grid, np.zeros_like(grid), color=color, label='Potential energy')
    ax_energy.legend(loc='upper right')

    title_string = fig.suptitle('')

    ax_string.set_xlim(0, size-1)
    ax_string.set_ylim(-1.1, 1.1)
    ax_energy.set_xlim(.5, size-.5)
    Ek0, Ep0 = get_energies(result.y[:, 0])
    
    ax_energy.set_ylim(0, sum(Ek0)+sum(Ep0))
    ax_string.set_xlabel('Mass index')
    ax_energy.set_xlabel('Normal mode index')
    for ax in [ax_string, ax_energy]:        
        ax.set_yticks([])
        if size < 20:
            ax.set_xticks(grid)

    def plot_frame(i):

        line.set_data(grid, result.y[:size, i])
        Ek, Ep = get_energies(result.y[:, i])

        for j, b in enumerate(bars_p):
            b.set_y(0)
            b.set_height(Ep[j])

        for j, b in enumerate(bars_k):
            b.set_y(Ep[j])
            b.set_height(Ek[j])

        time = result.t[i] / t_1
        title = f'$t = {time:.2f} T_1$' + label
        title_string.set_text(title)

        return iter([line, *bars_k, *bars_p, title_string])

    anim = animation.FuncAnimation(
        fig, 
        plot_frame, 
        frames=n_frames, 
        interval=1000/60,
        blit=True,
    )
    anim.save(fname)

def linear_system():

    m = 1.
    k = 1.
    J = 64

    x = np.linspace(0,1,J+1)

    def fun(t, yyp):
        y = yyp[:J+1]
        yp = yyp[J+1:]

        acc = y*0.
        acc[1:-1] = k/m * (y[2:]-2*y[1:-1]+y[:-2])
        
        return np.concatenate((yp, acc))

    # simulate for one full cycle of the fundamental
    tmax = 2 * np.pi / (2 * k/m*np.sin(np.pi / 2 / J))

    n_frames = 200

    result_fundamental = solve_ivp(
        fun, 
        t_span=(0, tmax), 
        t_eval=np.linspace(0, tmax*(1-1/n_frames), num=n_frames), 
        y0=np.concatenate((np.sin(np.pi*x), np.zeros_like(x))), 
        method='RK45'
    )
    result_harmonic = solve_ivp(
        fun, 
        t_span=(0, tmax), 
        t_eval=np.linspace(0, tmax*(1-1/n_frames), num=n_frames), 
        y0=np.concatenate((np.sin(2*np.pi*x), np.zeros_like(x))), 
        method='RK45'
    )

    rng = np.random.default_rng(seed=1)

    result_random = solve_ivp(
        fun, 
        t_span=(0, tmax), 
        t_eval=np.linspace(0, tmax*(1-1/n_frames), num=n_frames), 
        y0=np.concatenate((
            [0],
            np.convolve(
                rng.normal(scale=0.1, size=J-1),
                np.ones(8), 
                mode='same'
            ), 
            [0],
            np.zeros_like(x))), 
        method='RK45'
    )

    results = {
        'fundamental': result_fundamental,
        'harmonic': result_harmonic,
        'random': result_random,
    }
    colors = {
        'fundamental': '#1E88E5',
        'harmonic': '#D81B60',
        'random': '#FFC107'
    }

    plot_oscillation(results, colors, Path('linear.gif'))

def non_linear_system(
    initial_condition, 
    video_path=Path('nonlinear.mp4'), 
    alpha=0., 
    beta=0., 
    periods=1,
    frames_per_period=300,
    label=None,
    ):

    m = 1.
    k = 1.
    
    J = len(initial_condition) - 1

    x = np.linspace(0,1,J+1)
    grid = np.arange(J+1)

    def fun(t, yyp, alpha, beta):
        y = yyp[:J+1]
        yp = yyp[J+1:]

        acc = y*0.
        
        # index i == [1:-1]
        # index i-1 == [:-2]
        # index i+1 == [2:]
        
        acc[1:-1] = k/m * (
            (y[2:]-2*y[1:-1]+y[:-2])
            + alpha*(
                (y[2:] - y[1:-1])**2 - 
                (y[1:-1] - y[:-2])**2
            )
            + beta*(
                (y[2:] - y[1:-1])**3 - 
                (y[1:-1] - y[:-2])**3
            )
        )
        
        return np.concatenate((yp, acc))

    # simulate for many full cycles of the fundamental
    
    tmax = 2 * np.pi / (
        2 * k/m
        * np.sin(np.pi / 2 / J)
    ) * periods

    n_frames = frames_per_period * int(periods)
    
    solver_kwargs = {
        't_eval':np.linspace(0, tmax*(1-1/n_frames), num=n_frames), 
        'y0':np.concatenate((initial_condition, np.zeros_like(x))), 
        't_span':(0, tmax), 
        'method':'RK45',
    }
    
    result = solve_ivp(
        fun, 
        args=(alpha, beta),
        **solver_kwargs
    )
    
    plot_oscillation_and_energy(result, '#D81B60', video_path, label=label)
    
if __name__ == '__main__':
    # linear_system()
    
    # t_rec = recurrence_periods(J, alpha, 1.)


    rng = np.random.default_rng(seed=1)

    y_random = np.concatenate((
        [0],
        np.convolve(
            rng.normal(size=2**7-1),
            stats.norm.pdf(np.linspace(-3, 3, num=20)), 
            mode='same'
        ), 
        [0],
    ))
    y_random /= y_random.max()
    y_random *= 0.8

    non_linear_system(
        y_random,
        periods=2,
        alpha=0.,
        video_path=Path('random_y0.mp4'),
        label=', random initial conditions',
        frames_per_period=1000,
    )
    
    non_linear_system(
        np.sin(np.pi*np.linspace(0, 1, 2**5+1)),
        periods=10,
        alpha=1,
        video_path=Path('alpha_1.mp4'),
        label=', $\\alpha=1$',
    )