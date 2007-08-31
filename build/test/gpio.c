/* $NetBSD: gpioctl.c,v 1.1 2005/09/27 02:54:27 jmcneill Exp $ */
/*	$OpenBSD: gpioctl.c,v 1.2 2004/08/08 00:05:09 deraadt Exp $	*/
/*
 * Copyright (c) 2004 Alexander Yurchenko <grange@openbsd.org>
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

/*
 * Program to control GPIO devices.
 */

#include <sys/types.h>
#include <sys/gpio.h>
#include <sys/ioctl.h>

#include <err.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

extern int devfd;

void	pinread(int);
void	pinwrite(int, int);

void
pinread(int pin)
{
	struct gpio_pin_op op;

	bzero(&op, sizeof(op));
	op.gp_pin = pin;
	if (ioctl(devfd, GPIOPINREAD, &op) == -1)
		err(1, "GPIOPINREAD");
	return;
}

void
pinwrite(int pin, int value)
{
	struct gpio_pin_op op;

	if (value < 0 || value > 2)
		errx(1, "%d: invalid value", value);

	bzero(&op, sizeof(op));
	op.gp_pin = pin;
	op.gp_value = (value == 0 ? GPIO_PIN_LOW : GPIO_PIN_HIGH);
	if (value < 2) {
		if (ioctl(devfd, GPIOPINWRITE, &op) == -1)
			err(1, "GPIOPINWRITE");
	} else {
		if (ioctl(devfd, GPIOPINTOGGLE, &op) == -1)
			err(1, "GPIOPINTOGGLE");
	}
	return;
}

