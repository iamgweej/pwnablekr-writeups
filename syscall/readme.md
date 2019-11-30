# Syscall

Finally, some kernel exploitation!

Well, we can see the problem here:

```c
asmlinkage long sys_upper(char *in, char* out){
	int len = strlen(in);
	int i;
	for(i=0; i<len; i++){
		if(in[i]>=0x61 && in[i]<=0x7a){
			out[i] = in[i] - 0x20;
		}
		else{
			out[i] = in[i];
		}
	}
	return 0;
}
```

We can write basically anything to anywhere in the kernel. So what now?

My idea was like this: we override another entry of the syscall table, and point it towards a function giving our process `root` privilages. We'll just compile our malicous executable so its `.text` section lies in non-lowercase address space.

Using `/proc/kallsyms`, I was able to find the addresses of the kernel-functions `commit_creds()` and `prepare_kernel_cred`, which I used to get `root`. 

I then used `ld --verbose` to get the default loading script, and then I patched it to map my `.text` section to `0x41418000`, which allowed me to point the 224th entry of the syscall table to my `sys_pe` function. Victory!
