# make -C native        → src/algos/_native/libalgos.so
OUT    := ../src/algos/_native/libalgos.so
CFLAGS := -O3 -march=native -fPIC -shared -Wall -Wextra

$(OUT): c/*.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(OUT)

.PHONY: clean
