#!/usr/bin/python3
import os, sys, subprocess, base64, webbrowser
import matplotlib.pyplot as plt
from random import random

_thisdir = os.path.split(os.path.abspath(__file__))[0]

ZIG = os.path.join(_thisdir, 'zig-linux-x86_64-0.13.0/zig')
C3 = '/usr/local/bin/c3c'
EMCC = 'emcc'

islinux=iswindows=isapple=c3gz=c3zip=None
if sys.platform == 'win32':
	c3zip = 'https://github.com/c3lang/c3c/releases/download/latest/c3-windows.zip'
	C3 = os.path.join(_thisdir,'c3/c3c.exe')
	iswindows=True
elif sys.platform == 'darwin':
	c3zip = 'https://github.com/c3lang/c3c/releases/download/latest/c3-macos.zip'
	isapple=True
else:
	c3gz = 'https://github.com/c3lang/c3c/releases/download/latest/c3-ubuntu-20.tar.gz'
	islinux=True

if not os.path.isfile(ZIG):
	if not os.path.isfile('zig-linux-x86_64-0.13.0.tar.xz'):
		cmd = 'wget -c https://ziglang.org/download/0.13.0/zig-linux-x86_64-0.13.0.tar.xz'
		print(cmd)
		subprocess.check_call(cmd.split())
	cmd = 'tar -xvf zig-linux-x86_64-0.13.0.tar.xz'
	print(cmd)
	subprocess.check_call(cmd.split())


if not os.path.isfile(C3):
	C3 = '/opt/c3/c3c'
	if not os.path.isfile(C3):
		if not os.path.isdir('./c3'):
			if c3gz:
				if not os.path.isfile('c3-ubuntu-20.tar.gz'):
					cmd = 'wget -c %s' % c3gz
					print(cmd)
					subprocess.check_call(cmd.split())
				cmd = 'tar -xvf c3-ubuntu-20.tar.gz'
				print(cmd)
				subprocess.check_call(cmd.split())
			elif c3zip and iswindows:
				if not os.path.isfile('c3-windows.zip'):
					cmd = ['C:/Windows/System32/curl.exe', '-o', 'c3-windows.zip', c3zip]
					print(cmd)
					subprocess.check_call(cmd)
			elif c3zip:
				if not os.path.isfile('c3-macos.zip'):
					cmd = ['curl', '-o', 'c3-macos.zip', c3zip]
					print(cmd)
					subprocess.check_call(cmd)

		if islinux:
			C3 = os.path.abspath('./c3/c3c')
		elif iswindows:
			C3 = os.path.abspath('./c3/c3c.exe')

assert os.path.isfile(C3)
print('c3c:', C3)


def zig_compile(zig, name='test-zig', freestanding=True, info={}):
	ver = subprocess.check_output([ZIG, 'version']).decode('utf-8').strip()
	print('zig version:', ver)
	info['zig'] = ver


	tmp = '/tmp/%s.zig' % name
	open(tmp,'w').write(zig)

	cmd = [ZIG, 'build-exe']
	target = 'wasm32-wasi'
	if freestanding:
		target = 'wasm32-freestanding-musl'

	cmd += [
		'-O', 'ReleaseSmall', '-target', target,  
		'-fno-entry',
		'--export-table', '-rdynamic',
		tmp
	]
	print(cmd)
	subprocess.check_call(cmd, cwd='/tmp')

	return '/tmp/%s.wasm' % name


def c3_version(c3):
	ver = subprocess.check_output([c3, '--version']).decode('utf-8')
	#print('c3 version:', ver)
	v = ''
	for ln in ver.splitlines():
		if ln.startswith('C3 Compiler Version:'):
			print(ln)
			v += ln.split('C3 Compiler Version:')[-1].split('(')[0].strip()
		#elif ln.startswith('LLVM version:'):
		#	v += ' LLVM=' + ln.split('LLVM version:')[-1].strip()
	return v


def c3_compile(c3, name='test-c3', info={}):
	info['c3']=c3_version(C3)
	tmp = '/tmp/%s.c3' % name
	open(tmp,'w').write(c3)
	cmd = [
		C3, '--target', 'wasm32', 'compile',
		'--output-dir', '/tmp',
		'--obj-out', '/tmp',
		'--build-dir', '/tmp',
		#'--print-output',
		'--link-libc=no', '--use-stdlib=no', '--no-entry', '--reloc=none', '-z', '--export-table',
		'-Oz',
		'-o', name,
		tmp
	]
	print(cmd)
	subprocess.check_call(cmd)
	return '/tmp/%s.wasm' % name

def emcc_version(emcc):
	ver = subprocess.check_output([emcc, '--version']).decode('utf-8')
	ver = ver.splitlines()[0]
	assert ver.startswith('emcc')
	if ver.endswith('()'):
		ver = ver[:-2].strip()
	print(ver)
	ver = ver.split()[-1]
	return ver

def c_compile(c, name='test-c', info={}):
	info['c'] = emcc_version(EMCC)
	tmp = '/tmp/%s.c' % name
	open(tmp,'w').write(c)
	output = '/tmp/%s.wasm32' % name
	cmd = [
		EMCC, '-o', output, 
		"-s","WASM=1",
		'-s', 'ERROR_ON_UNDEFINED_SYMBOLS=0',
		'-rdynamic',
		'-Oz',
		tmp
	]
	print(cmd)
	subprocess.check_call(cmd)
	return '/tmp/%s.wasm' % name

rand_floats = [str(random()) for i in range(1024)]

TESTS = {
	'helloworld':{
		'zig': '''
extern fn printn(
	ptr: [*]const u8, 
	len:c_int
	) void;

export fn main() void {
	printn("hello world", 11);
}
		''',
		'c3':'''
extern fn void printn(
	char *ptr, 
	int len
	);

fn void main() 
	@extern("main") 
	@wasm {
	printn("hello world", 11);
}
		''',

		'c':'''
extern void printn(
	char *ptr, 
	int len
	);

void main(){
	printn("hello world", 11);
}
		''',

		'js':'''
console.log("hello world");
		''',

		'JS':'''
printn(ptr, len){
	const b=new Uint8Array(this.wasm.instance.exports.memory.buffer,ptr,len);
	window.alert(new TextDecoder().decode(b));
}
		'''


	},

	## test 2 ##
	'embed float32 array 8' : {
		'zig':'''
extern fn print_array(
	ptr: [*]const f32, 
	len:c_int
	) void;

const arr : [8]f32 = .{
	1.0,2.0,3.0,4.0,
	5.0,6.0,7.0,8.0};

export fn main() void {
	print_array(&arr, 8);
}
		''',

		'c3':'''
extern fn void print_array(
	float *ptr, 
	int len
	);

float[8] arr = {
	1.0,2.0,3.0,4.0,
	5.0,6.0,7.0,8.0};

fn void main() 
	@extern("main") 
	@wasm {
	print_array(&arr, 8);
}
		''',

		'c':'''
extern void print_array(
	float *ptr, 
	int len
	);

float arr[8] = {
	1.0,2.0,3.0,4.0,
	5.0,6.0,7.0,8.0};

void main() {
	print_array(&arr, 8);
}
		''',

		'js':'''
var arr = [
	1.0,2.0,3.0,4.0,
	5.0,6.0,7.0,8.0];

console.log(arr);
		'''

	},

	## test 3 ##
	'embed float32 array %s' % len(rand_floats) : {
		'zig':'''
extern fn print_array(
	ptr: [*]const f32, 
	len:c_int
	) void;

const arr : [%s]f32 = .{%s};

export fn main() void {
	print_array(&arr, %s);
}
		''' % (len(rand_floats), ','.join(rand_floats), len(rand_floats)),

		'c3':'''
extern fn void print_array(
	float *ptr, 
	int len
	);

float[%s] arr = {%s};

fn void main() 
	@extern("main") 
	@wasm {
	print_array(&arr, %s);
}
		''' % (len(rand_floats), ','.join(rand_floats), len(rand_floats)),
	},


	## test 4 ##
	'embed float16 array %s' % len(rand_floats) : {
		'zig':'''
extern fn print_array(
	ptr: [*]const f16, 
	len:c_int
	) void;

const arr : [%s]f16 = .{%s};

export fn main() void {
	print_array(&arr, %s);
}
		''' % (len(rand_floats), ','.join(rand_floats), len(rand_floats)),

		'c3':'''
extern fn void print_array(
	float16 *ptr, 
	int len
	);

float16[%s] arr = {%s};

fn void main() 
	@extern("main") 
	@wasm {
	print_array(&arr, %s);
}
		''' % (len(rand_floats), ','.join(rand_floats), len(rand_floats)),
	}


}


JS_API = '''
function make_environment(e){
	return new Proxy(e,{
		get(t,p,r) {
			if(e[p]!==undefined){return e[p].bind(e)}
			return(...args)=>{throw p}
		}
	});
}
class api{
	proxy(){
		return make_environment(this)
	}
	reset(wasm){
		this.wasm=wasm;
		this.wasm.instance.exports.main();
	}


'''

JS_DECOMP = '''
var $d=async(u,t)=>{
	var d=new DecompressionStream('gzip')
	var r=await fetch('data:application/octet-stream;base64,'+u)
	var b=await r.blob()
	var s=b.stream().pipeThrough(d)
	var o=await new Response(s).blob()
	if(t) return await o.text()
	else return await o.arrayBuffer()
}
$d($wasm).then((r)=>{
	WebAssembly.instantiate(r,{env:$.proxy()}).then((c)=>{$.reset(c)});
});
'''



def gen_js_api(wasm, methods):
	cmd = ['gzip', '--keep', '--force', '--verbose', '--best', wasm]
	print(cmd)
	subprocess.check_call(cmd)
	wa = open(wasm,'rb').read()
	w = open(wasm+'.gz','rb').read()
	b = base64.b64encode(w).decode('utf-8')

	js = [
		JS_API,
		methods,
		'};',
		'$=new api();',
		'var $wasm="%s";' % b,
		JS_DECOMP,
	]
	return '\n'.join(js)

def run_tests():
	for name in TESTS:
		print('test:', name)
		t = TESTS[name]
		info = {}
		wasms = {}
		overlays = []
		if 'zig' in t:
			wasm = zig_compile(t['zig'], info=info)
			wasms['zig']=wasm
			overlays.append(t['zig'])

			if os.path.isfile('/usr/bin/wasm-opt'):
				opt = wasm.replace('.wasm', '.opt.wasm')
				cmd = ['wasm-opt', '-o', opt, '-Oz', wasm]
				print(cmd)
				subprocess.check_call(cmd)
				overlays.append(None)
				wasms['zig.wasm-opt'] = opt

			if 'JS' in t and '--test' in sys.argv:
				test_wasm(wasm, t['JS'], title='zig - %s' % name)


		if 'c3' in t:
			wasm = c3_compile(t['c3'], info=info)
			wasms['c3']=wasm
			overlays.append(t['c3'])

			if os.path.isfile('/usr/bin/wasm-opt'):
				opt = wasm.replace('.wasm', '.opt.wasm')
				cmd = ['wasm-opt', '-o', opt, '-Oz', wasm]
				print(cmd)
				subprocess.check_call(cmd)
				overlays.append(None)
				wasms['c3.wasm-opt'] = opt


			if 'JS' in t and '--test' in sys.argv:
				test_wasm(wasm, t['JS'], title='c3 - %s' % name)


		if 'c' in t and '--c' in sys.argv:
			wasm = c_compile(t['c'], info=info)
			wasms['c']=wasm
			overlays.append(t['c'])
			if 'JS' in t and '--test-todo' in sys.argv:
				## TODO: Uncaught (in promise) TypeError: import object field 'a' is not an Object 
				test_wasm(wasm, t['JS'], title='c - %s' % name)

		if 'js' in t and '--js' in sys.argv:
			tmp = '/tmp/%s.js' % name
			open(tmp,'w').write(t['js'])
			wasms['javascript'] = tmp
			overlays.append(t['js'])

	
		os.system('ls -l %s' % ' '.join(wasms.values()))
		print(info)
		names = []
		for k in wasms:
			if k in info:
				if k=='c':
					names.append('%s %s' %('emcc', info[k]))
				else:
					names.append('%s %s' %(k, info[k]))
			else:
				names.append(k)

		values = [len(open(f,'rb').read()) for f in wasms.values()]
		fig, ax = plt.subplots()
		ax.set_title(name)
		ax.set_ylabel('wasm: bytes')
		colors = ['cyan', 'cyan', 'orange', 'orange']
		ax.bar(names, values, color=colors)

		for i,rect in enumerate(ax.patches):
			x = rect.get_x()
			ax.text(x, rect.get_height(), '%s bytes' % values[i], fontsize=10)

			if not overlays[i]:
				continue
			y = rect.get_y() + (rect.get_height()/3)
			txt = overlays[i].strip().replace('\t', '  ')
			if txt:
				tx = []
				for ln in txt.splitlines():
					if len(ln) > 50:
						ln = ln[:45] + '...'
					tx.append(ln)
				txt = '\n'.join(tx)
				ax.text(x, y, txt+'\n', fontsize=12)

		plt.show()
		if '--test-hello' in sys.argv:
			break



def test_wasm(wasm, methods, title='test'):
	o = [
		'<html>',
		'<body>',
		'<h2>%s</h2>' % title,
		'<script>',
		gen_js_api(wasm, methods),
		'</script>',
		'</body>',
		'</html>',
	]
	out = '%s.html' % title
	open(out,'w').write('\n'.join(o))
	webbrowser.open(out)


if __name__=='__main__':
	run_tests()
