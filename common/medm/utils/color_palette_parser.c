#include <stdio.h>

int main(int argc, char *argv[]) {
  FILE *fp;
  char fname[] = argv[1];

  fp = fopen(fname, "r");
  if(fp == NULL) {
    printf("%s file not open!\n", fname);
    return -1;
  } else {
    printf("Opened file: %s\n", fname);
  }

  
};  
