#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#define NR_LOOPS 5
#define FLUSH_SIZE 64*1024*1024

double pc_freq = 0.0;
void init_timer()
{
    LARGE_INTEGER li;
    if(QueryPerformanceFrequency(&li)==NULL)
    {
        printf("Eroare la verificarea frecventei\n");
    }
    pc_freq=li.QuadPart*1.0;

}
double get_time_sec()
{
    LARGE_INTEGER li;
    QueryPerformanceCounter(&li);
    return li.QuadPart*1.0/pc_freq;
}
double access_seq(int *array, long long size, int repeat)
{
    volatile int sum=0;
    double start=get_time_sec();
    for(int r=0; r<repeat; r++)
    {
        for(long long  i=0; i<size; i++)
        {
            sum+=array[i];
        }
    }
    double end=get_time_sec();
    return (end-start)/repeat;
}
double access_ran(int *array, long long size, int *indices, int repeat)
{
    volatile int sum=0;
    double start=get_time_sec();
    for(int r=0; r<repeat; r++)
    {
        for(long long i=0; i<size; i++)
        {
            sum+=array[indices[i]];
        }
    }
    double end=get_time_sec();
    return (end-start)/repeat;
}
double access_matrix_row(int *array, int rows, int cols, int repeat)
{
    volatile int sum=0;
    double start=get_time_sec();
    for(int r=0; r<repeat; r++)
    {
        for(long long i=0; i<rows; i++)
        {
            int index_linie = i * cols;
            for(int j=0; j<cols; j++)
            {
                sum+=array[index_linie+j];
            }
        }
    }
    double end=get_time_sec();
    return (end-start)/repeat;
}
double access_matrix_col(int *array, int rows, int cols, int repeat)
{
    volatile int sum=0;
    double start=get_time_sec();
    for(int r=0; r<repeat; r++)
    {

        for(int j=0; j<cols; j++)
        {
            for(int i=0; i<rows; i++)
            {
                sum+=array[i*cols+j];
            }
        }
    }
    double end=get_time_sec();
    return (end-start)/repeat;
}
double access_matrix_fragmented(int **mat, int rows, int cols, int repeat)
{
    volatile int sum=0;
    double start=get_time_sec();
    for(int r=0; r<repeat; r++)
    {
        for(int i=0; i<rows; i++)
        {
            for(int j=0; j<cols; j++)
            {
                sum+=mat[i][j];
            }
        }
    }
    double end=get_time_sec();
    return (end-start)/repeat;

}
void flush_cache()
{
    static char *str=NULL;
    if(str==NULL)
    {
        str=(char*)malloc(FLUSH_SIZE);
        if(str==NULL)
        {
            return;
        }
    }
    for(int i=0; i<FLUSH_SIZE; i++)
    {
        str[i]++;
    }
}
int main(int argc, char *argv[])
{
    char *pEnd;
    long long limit_size=8192LL*1024*1024;
    int t_sec=1, t_ran=1, t_row=1, t_col=1, t_frag=1;
    if(argc>=7)
    {
        limit_size=strtoll(argv[1], &pEnd, 10);
        t_sec=atoi(argv[2]);
        t_ran=atoi(argv[3]);
        t_row=atoi(argv[4]);
        t_col=atoi(argv[5]);
        t_frag=atoi(argv[6]);
    }
    init_timer();
    long long sizes[]= {4*1024, 16*1024, 64*1024, 256*1024,
                        1024*1024, 4*1024*1024, 16*1024*1024,
                        64*1024*1024, 256*1024*1024, 512*1024*1024,
                        1024LL*1024*1024, 2048LL*1024*1024,
                        4096LL*1024*1024, 8192LL*1024*1024,
                       };
    FILE *f=fopen("rezultate.csv", "w");
    if(f==NULL)
    {
        perror("Could not open csv file");
        return -1;
    }
    fprintf(f, "Dimensiune(bytes),Tip,Timp(s),Viteza(MB/s)\n");

    int repeat;
    int n_sizes = sizeof(sizes)/sizeof(sizes[0]);
    for(int i=0; i<n_sizes; i++)
    {
        if(sizes[i]>limit_size)
        {
            break;
        }
        if(sizes[i]<=64*1024)
        {
            repeat=10000;
        }
        else
        {
            if(sizes[i]<=1024*1024)
            {
                repeat=1000;
            }
            else
            {
                repeat=5;
            }
        }
        long long display_value;
        char *unit;
        if(sizes[i]<1024*1024)
        {
            display_value=sizes[i]/1024;
            unit="KB";
        }
        else
        {
            display_value=sizes[i]/1024/1024;
            unit="MB";
        }
        printf("STARE: Incep testul cu %lld %s...\n", display_value, unit);
        fflush(stdout);

        long long length=sizes[i]/sizeof(int);
        int *array=malloc(length*sizeof(int));
        int *indices=NULL;
        if(t_ran)
        {
            indices=malloc(length*sizeof(int));
        }
        if(array==NULL || (t_ran && indices==NULL))
        {
            printf("STARE: Memorie insuficienta, sar peste.\n");
            fflush(stdout);
            perror("Nu pot aloca memorie pentru siruri\n");
            free(array);
            free(indices);
            continue;
        }

        for(long long l=0; l<length; l++)
        {
            array[l]=rand();
            if(t_ran)
            {
                indices[l]=l;
            }
        }
        if(t_ran)
        {
            for(long long l=length-1; l>0; l--)
            {
                int j=rand()%(l+1);
                int aux=indices[l];
                indices[l]=indices[j];
                indices[j]=aux;
            }
        }
        if(t_sec)
        {
            printf("STARE: [%lld %s] Rulez acces secvential...\n", display_value, unit);
            fflush(stdout);
            double time_seq=0;
            for(int r=0; r<NR_LOOPS; r++)
            {
                flush_cache();
                time_seq+=access_seq(array, length, repeat);
            }
            double avg_time_seq=time_seq/NR_LOOPS;
            double speed_seq=sizes[i]/(1024*1024*avg_time_seq);
            fprintf(f, "%lld,Secvential,%.4f,%.2f\n", sizes[i], avg_time_seq, speed_seq);
        }

        if(t_ran)
        {
            printf("STARE: [%lld %s] Rulez acces aleator...\n", display_value, unit);
            fflush(stdout);
            double time_ran=0;
            for(int r=0; r<NR_LOOPS; r++)
            {
                flush_cache();
                time_ran+=access_ran(array, length, indices, repeat);
            }
            double avg_time_ran=time_ran/NR_LOOPS;
            double speed_ran=sizes[i]/(1024*1024*avg_time_ran);
            fprintf(f, "%lld,Aleator,%.4f,%.2f\n", sizes[i], avg_time_ran, speed_ran);
        }
        int cols=1024;
        if(length<cols)
        {
            cols = length;
        }
        int rows=length/cols;

        if(t_row)
        {
            printf("STARE: [%lld %s] Rulez matrice linii...\n", display_value, unit);
            fflush(stdout);
            double time_row=0;
            for(int r=0; r<NR_LOOPS; r++)
            {
                flush_cache();
                time_row+=access_matrix_row(array, rows, cols, repeat);
            }
            double avg_time_row=time_row/NR_LOOPS;
            double speed_row=sizes[i]/(1024*1024*avg_time_row);
            fprintf(f, "%lld,Matrice-Linii,%.4f,%.2f\n", sizes[i], avg_time_row, speed_row);
        }
        if(t_col)
        {
            printf("STARE: [%lld %s] Rulez matrice coloane...\n", display_value, unit);
            fflush(stdout);
            double time_col=0;
            for(int r=0; r<NR_LOOPS; r++)
            {
                flush_cache();
                time_col+=access_matrix_col(array, rows, cols, repeat);
            }
            double avg_time_col=time_col/NR_LOOPS;
            double speed_col=sizes[i]/(1024*1024*avg_time_col);
            fprintf(f, "%lld,Matrice-Coloane,%.4f,%.2f\n", sizes[i], avg_time_col, speed_col);
        }

        free(array);
        free(indices);

        if(t_frag)
        {
            printf("STARE: [%lld %s] Rulez matrice fragmentata...\n", display_value, unit);
            fflush(stdout);
            int **mat = malloc(rows * sizeof(int*));
            if(mat==NULL)
            {
                return -1;
            }
            for(int l=0; l<rows; l++)
            {
                mat[l] = malloc(cols * sizeof(int));
                if(mat[l]==NULL)
                {
                    return -1;
                }
                for(int j=0; j<cols; j++)
                {
                    mat[l][j]=rand();
                }
            }
            for(int l=rows-1; l>0; l--)
            {
                int r_aleator=rand()%(l+1);
                int *aux=mat[l];
                mat[l]=mat[r_aleator];
                mat[r_aleator]=aux;
            }
            double time_frag=0;
            for(int r=0; r<NR_LOOPS; r++)
            {
                flush_cache();
                time_frag+=access_matrix_fragmented(mat, rows, cols, repeat);
            }
            double avg_time_frag=time_frag/NR_LOOPS;
            double speed_frag=sizes[i]/(1024*1024*avg_time_frag);
            fprintf(f, "%lld,Matrice-Fragmentata,%.4f,%.2f\n", sizes[i], avg_time_frag, speed_frag);

            for(int l=0; l<rows; l++)
            {
                free(mat[l]);
            }
            free(mat);
        }
    }
    fclose(f);
    printf("STARE: Gata\n");
    return 0;

}
