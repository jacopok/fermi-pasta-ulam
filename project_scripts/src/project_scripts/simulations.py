import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from IPython.display import HTML
from scipy.integrate import solve_ivp
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

def plot_oscillation_and_energy(result, color, fname):
    
    n_frames = len(result.t)
    size = result.y.shape[0] // 2
    grid = np.arange(size)
    
    i = np.arange(size)
    matrix = np.sqrt(2/size) * np.sin(i[:, np.newaxis] * i[np.newaxis, :] * np.pi / size)
    
    omegas = 2 * np.sin(np.pi * i / 2 / size)
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

    title_energy = ax_energy.set_title('Energy repartition')
    title_string = ax_string.set_title('')

    ax_string.set_xlim(0, size-1)
    ax_string.set_ylim(-1.1, 1.1)
    ax_energy.set_xlim(.5, size-.5)
    ax_energy.set_ylim(0, .2)
    ax_string.set_xlabel('Mass index')
    ax_energy.set_xlabel('Normal mode index')
    for ax in [ax_string, ax_energy]:        
        ax.set_yticks([])
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
        title_string.set_text(f'$t = {time:.2f} T_1$')

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

def non_linear_system():

    m = 1.
    k = 1.
    J = 16

    x = np.linspace(0,1,J+1)

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
    
    t_rec = recurrence_periods(J, 2., 1.)

    tmax = 2 * np.pi / (
        2 * k/m
        * np.sin(np.pi / 2 / J)
    ) * t_rec

    n_frames = 200 * t_rec
    
    # result_fundamental = solve_ivp(
    #     fun, 
    #     t_span=(0, tmax), 
    #     t_eval=np.linspace(0, tmax*(1-1/n_frames), num=n_frames), 
    #     y0=np.concatenate((np.sin(np.pi*x), np.zeros_like(x))), 
    #     args=(0., 0.),
    #     method='RK45'
    # )
    solver_kwargs = {
        't_eval':np.linspace(0, tmax*(1-1/n_frames), num=n_frames), 
        'y0':np.concatenate((np.sin(np.pi*x), np.zeros_like(x))), 
        't_span':(0, tmax), 
        'method':'RK45',
        'atol': 1e-5,
    }
    
    result_alpha = solve_ivp(
        fun, 
        args=(2., 0.),
        **solver_kwargs
    )
    
    # result_beta = solve_ivp(
    #     fun, 
    #     args=(0., 50.),
    #     **solver_kwargs
    # )
    # result_alpha_beta = solve_ivp(
    #     fun, 
    #     args=(3., 50.),
    #     **solver_kwargs
    # )

    results = {
        # 'alpha_beta': result_alpha_beta,
        'alpha': result_alpha,
        # 'beta': result_beta,
    }
    
    for key in results:
        print(results[key].status)
    
    colors = {
        'alpha_beta': '#1E88E5',
        'alpha': '#D81B60',
        'beta': '#FFC107'
    }

    # plot_oscillation(results, colors, Path('nonlinear.mp4'))
    plot_oscillation_and_energy(result_alpha, '#D81B60', Path('evolution_and_energy.mp4'))
    
if __name__ == '__main__':
    # linear_system()
    non_linear_system()